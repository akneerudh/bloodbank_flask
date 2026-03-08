# Bloodbank Flask

A blood bank management web application built with Python Flask and SQLite. Designed for hospital or clinic staff to manage donors, track donations, monitor blood stock, and handle blood requests through a simple browser-based interface.

## Features

- Register and manage blood donors
- Log blood donations per donor
- View current blood stock levels by blood type
- Submit and track blood requests
- Automatic stock updates on donation and request fulfillment
- Undo accidental donor deletions

## Tech Stack

- **Backend:** Python, Flask, SQLite3
- **Frontend:** Jinja2 templates, Bootstrap 5, vanilla CSS
- **Database:** SQLite (local file, no server required)

## Project Structure

```
bloodbank_flask/
    app.py                  # Main Flask application and all routes
    migrate_to_sqlite.py    # One-time migration script from MySQL to SQLite
    sqlite_commands.txt     # Reference guide for inspecting the database
    static/
        style.css           # Custom dark-themed styles
    templates/
        base.html           # Base layout with sidebar navigation
        index.html          # Dashboard
        add_donor.html      # Donor registration form
        add_donation.html   # Donation logging form
        view_donors.html    # Donor list with delete and undo
        view_stock.html     # Blood stock levels table
        request_blood.html  # Blood request form
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

1. Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/bloodbank-flask.git
cd bloodbank-flask
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux
```

3. Install dependencies:

```bash
pip install flask
```

4. Run the application:

```bash
python app.py
```

5. Open your browser and go to `http://127.0.0.1:5000`

## Database

The app creates a `bloodbank.db` SQLite file automatically on first run. No additional database setup is required.

If you are migrating from an existing MySQL database, update the connection details in `migrate_to_sqlite.py` and run:

```bash
python migrate_to_sqlite.py
```

## Notes

- The `bloodbank.db` file is excluded from version control via `.gitignore`
- The donor undo/delete history is stored in memory and resets on server restart
- The app is intended for local or internal network use and does not include authentication
