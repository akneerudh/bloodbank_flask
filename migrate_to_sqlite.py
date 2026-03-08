"""
Run this ONCE to migrate existing MySQL bloodbank data to SQLite.
Usage:
    python migrate_to_sqlite.py

It will create bloodbank.db in the same folder.
"""

import pymysql
import sqlite3
import os

SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'bloodbank.db')

# ── Connect to MySQL ──────────────────────────────────────────────
print("Connecting to MySQL...")
try:
    my = pymysql.connect(
        host="localhost",
        user="root",
        passwd="Iamandroid@2022",
        db="bloodbank",
        autocommit=True,
        cursorclass=pymysql.cursors.Cursor
    )
    mc = my.cursor()
    print("  MySQL connected.")
except Exception as e:
    print(f"  ERROR connecting to MySQL: {e}")
    raise

# ── Create / reset SQLite ─────────────────────────────────────────
if os.path.exists(SQLITE_PATH):
    os.remove(SQLITE_PATH)
    print(f"  Removed existing {SQLITE_PATH}")

sq = sqlite3.connect(SQLITE_PATH)
sc = sq.cursor()
print(f"  Created {SQLITE_PATH}")

# ── Schema ────────────────────────────────────────────────────────
print("Creating schema...")
sc.executescript("""
CREATE TABLE IF NOT EXISTS Donor (
    donor_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    dob        TEXT    NOT NULL,
    gender     TEXT    NOT NULL,
    blood_group TEXT   NOT NULL,
    phone      TEXT    NOT NULL,
    email      TEXT,
    address    TEXT
);

CREATE TABLE IF NOT EXISTS Donation (
    donation_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id     INTEGER NOT NULL,
    blood_group  TEXT    NOT NULL,
    units        REAL    NOT NULL,
    donation_date TEXT   DEFAULT (date('now')),
    FOREIGN KEY (donor_id) REFERENCES Donor(donor_id)
);

CREATE TABLE IF NOT EXISTS BloodStock (
    blood_group TEXT PRIMARY KEY,
    units       REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Request (
    request_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name  TEXT NOT NULL,
    blood_group   TEXT NOT NULL,
    units_required REAL NOT NULL,
    request_date  TEXT DEFAULT (date('now'))
);
""")
sq.commit()
print("  Schema created.")

# ── Migrate Donor ─────────────────────────────────────────────────
print("Migrating Donor...")
mc.execute("SELECT donor_id, name, dob, gender, blood_group, phone, email, address FROM Donor")
donors = mc.fetchall()
for row in donors:
    sc.execute(
        "INSERT INTO Donor (donor_id, name, dob, gender, blood_group, phone, email, address) VALUES (?,?,?,?,?,?,?,?)",
        (row[0], row[1], str(row[2]), row[3], row[4], row[5], row[6], row[7])
    )
sq.commit()
print(f"  {len(donors)} donors migrated.")

# ── Migrate Donation ──────────────────────────────────────────────
print("Migrating Donation...")
try:
    mc.execute("SELECT * FROM Donation")
    donations = mc.fetchall()
    for row in donations:
        if len(row) == 4:
            sc.execute(
                "INSERT INTO Donation (donation_id, donor_id, blood_group, units) VALUES (?,?,?,?)",
                row
            )
        else:
            sc.execute(
                "INSERT INTO Donation (donation_id, donor_id, blood_group, units, donation_date) VALUES (?,?,?,?,?)",
                row[:5]
            )
    sq.commit()
    print(f"  {len(donations)} donations migrated.")
except Exception as e:
    print(f"  WARNING: Donation table issue: {e}")

# ── Migrate BloodStock ────────────────────────────────────────────
print("Migrating BloodStock...")
mc.execute("SELECT blood_group, units FROM BloodStock")
stock = mc.fetchall()
for row in stock:
    sc.execute("INSERT INTO BloodStock (blood_group, units) VALUES (?,?)", row)
sq.commit()
print(f"  {len(stock)} stock rows migrated.")

# ── Migrate Request ───────────────────────────────────────────────
print("Migrating Request...")
try:
    mc.execute("SELECT * FROM Request")
    requests = mc.fetchall()
    for row in requests:
        sc.execute(
            "INSERT INTO Request (request_id, patient_name, blood_group, units_required) VALUES (?,?,?,?)",
            row[:4]
        )
    sq.commit()
    print(f"  {len(requests)} requests migrated.")
except Exception as e:
    print(f"  WARNING: Request table issue: {e}")

# ── Verify ────────────────────────────────────────────────────────
print("\nVerification:")
for table in ['Donor', 'Donation', 'BloodStock', 'Request']:
    sc.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"  {table}: {sc.fetchone()[0]} rows")

my.close()
sq.close()
print("\nMigration complete! bloodbank.db is ready.")
