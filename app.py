from flask import Flask, render_template, request, redirect, g
import sqlite3
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bloodbank.db')

# Store deleted donors for undo functionality
deleted_donors_stack = []


# -- DB helpers --

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# -- Routes --

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/add_donor', methods=['GET', 'POST'])
def add_donor():
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        dob         = request.form.get('dob', '').strip()
        gender      = request.form.get('gender', '').strip()
        blood_group = request.form.get('blood_group', '').strip()
        phone       = request.form.get('phone', '').strip()
        email       = request.form.get('email', '').strip()
        address     = request.form.get('address', '').strip()

        phone_digits = ''.join(c for c in phone if c.isdigit())
        if len(phone_digits) != 10:
            error = "Phone number must be exactly 10 digits."
            return render_template('add_donor.html', error=error,
                                   name=name, dob=dob, gender=gender,
                                   blood_group=blood_group, phone=phone,
                                   email=email, address=address)

        db = get_db()

        existing = db.execute("SELECT donor_id FROM Donor WHERE phone = ?", (phone_digits,)).fetchone()
        if existing:
            error = "Phone number is already registered."
            return render_template('add_donor.html', error=error,
                                   name=name, dob=dob, gender=gender,
                                   blood_group=blood_group, phone=phone,
                                   email=email, address=address)

        if not dob:
            error = "Date of birth is required."
            return render_template('add_donor.html', error=error,
                                   name=name, dob=dob, gender=gender,
                                   blood_group=blood_group, phone=phone,
                                   email=email, address=address)

        try:
            dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
        except ValueError:
            error = "Date of birth must be in YYYY-MM-DD format."
            return render_template('add_donor.html', error=error,
                                   name=name, dob=dob, gender=gender,
                                   blood_group=blood_group, phone=phone,
                                   email=email, address=address)

        age = (datetime.today().date() - dob_date).days // 365
        if age < 18:
            error = f"Donor must be at least 18 years old. Current age: {age} years."
            return render_template('add_donor.html', error=error,
                                   name=name, dob=dob, gender=gender,
                                   blood_group=blood_group, phone=phone,
                                   email=email, address=address)

        db.execute(
            "INSERT INTO Donor (name, dob, gender, blood_group, phone, email, address) VALUES (?,?,?,?,?,?,?)",
            (name, dob, gender, blood_group, phone_digits, email, address)
        )
        db.commit()
        return redirect('/view_stock')

    return render_template("add_donor.html")


@app.route('/add_donation', methods=['GET', 'POST'])
def add_donation():
    db = get_db()

    if request.method == 'POST':
        donor_id    = request.form['donor_id']
        blood_group = request.form['blood_group']
        units_raw   = request.form.get('units', '').strip()

        try:
            units_val = float(units_raw)
        except ValueError:
            donors = db.execute("SELECT donor_id, name, blood_group FROM Donor").fetchall()
            return render_template("add_donation.html", donors=donors,
                                   error="Units must be a numeric value.")

        if units_val <= 0:
            donors = db.execute("SELECT donor_id, name, blood_group FROM Donor").fetchall()
            return render_template("add_donation.html", donors=donors,
                                   error="Units must be greater than zero.")

        if float(units_val).is_integer():
            units_val = int(units_val)

        donor = db.execute("SELECT dob FROM Donor WHERE donor_id = ?", (donor_id,)).fetchone()
        if donor:
            try:
                dob_date = datetime.strptime(str(donor[0]), '%Y-%m-%d').date()
                age = (datetime.today().date() - dob_date).days // 365
                if age < 18:
                    donors = db.execute("SELECT donor_id, name, blood_group FROM Donor").fetchall()
                    return render_template("add_donation.html", donors=donors,
                                           error=f"Donor must be at least 18 years old. Current age: {age} years.")
            except ValueError:
                pass

        db.execute(
            "INSERT INTO Donation (donor_id, blood_group, units) VALUES (?,?,?)",
            (donor_id, blood_group, units_val)
        )
        db.execute("""
            INSERT INTO BloodStock (blood_group, units) VALUES (?, ?)
            ON CONFLICT(blood_group) DO UPDATE SET units = units + excluded.units
        """, (blood_group, units_val))
        db.commit()
        return redirect('/view_stock')

    donors = db.execute("SELECT donor_id, name, blood_group FROM Donor").fetchall()
    return render_template("add_donation.html", donors=donors)


@app.route('/view_stock')
def view_stock():
    db = get_db()
    stock = db.execute("SELECT blood_group, units FROM BloodStock").fetchall()
    return render_template("view_stock.html", stock=stock)


@app.route('/view_donors')
def view_donors():
    db = get_db()
    donors = db.execute("SELECT * FROM Donor").fetchall()
    undo_available = len(deleted_donors_stack) > 0
    return render_template("view_donors.html", donors=donors, undo_available=undo_available)


@app.route('/delete_donor/<int:donor_id>', methods=['POST'])
def delete_donor(donor_id):
    db = get_db()
    donor_info = db.execute("SELECT * FROM Donor WHERE donor_id = ?", (donor_id,)).fetchone()
    if donor_info:
        deleted_donors_stack.append(tuple(donor_info))
        db.execute("DELETE FROM Donor WHERE donor_id = ?", (donor_id,))
        db.commit()
    return redirect('/view_donors')


@app.route('/undo_delete', methods=['POST'])
def undo_delete():
    if deleted_donors_stack:
        donor_info = deleted_donors_stack.pop()
        db = get_db()
        db.execute(
            "INSERT INTO Donor (donor_id, name, dob, gender, blood_group, phone, email, address) VALUES (?,?,?,?,?,?,?,?)",
            donor_info
        )
        db.commit()
    return redirect('/view_donors')


@app.route('/request_blood', methods=['GET', 'POST'])
def request_blood():
    if request.method == 'POST':
        patient     = request.form['patient']
        blood_group = request.form['blood_group']
        units       = int(request.form['units'])

        db = get_db()
        stock = db.execute("SELECT units FROM BloodStock WHERE blood_group = ?", (blood_group,)).fetchone()
        units_available = stock[0] if stock else 0

        if units > units_available:
            return render_template('request_blood.html',
                                   error=f"Requested units not available. Available: {units_available} units")

        db.execute(
            "INSERT INTO Request (patient_name, blood_group, units_required) VALUES (?,?,?)",
            (patient, blood_group, units)
        )
        db.execute(
            "UPDATE BloodStock SET units = units - ? WHERE blood_group = ?",
            (units, blood_group)
        )
        db.commit()
        return redirect('/view_stock')

    return render_template("request_blood.html")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8000)
