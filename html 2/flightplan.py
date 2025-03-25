from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from flask_session import Session
from argon2 import PasswordHasher

app = Flask(__name__)

# Secret key for session management
app.secret_key = "supersecretkey"

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Database connection details
DB_CONFIG = {
    'host': 'te3xi.h.filess.io',
    'port': 61002,
    'user': 'FLIGHTS_usingrate',
    'password': '6d8c67d4b9c0ea31f7312b543c6b73c418398d7d',
    'database': 'FLIGHTS_usingrate'
}

# Initialize Argon2 PasswordHasher
ph = PasswordHasher()

# Hardcoded Admin Credentials (hashed password)
ADMIN_USERNAME = "alnvb"
ADMIN_PASSWORD_HASH = ph.hash("password123")  # Store the Argon2 hashed password

# Ensure the database has the required table
def initialize_database():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flight_plans (
                id INT AUTO_INCREMENT PRIMARY KEY,
                flightnum VARCHAR(10),
                aircrafttype VARCHAR(10),
                departure VARCHAR(10),
                arrival VARCHAR(10),
                route TEXT,
                flight_rules VARCHAR(3),
                time_submitted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status ENUM('Inactive', 'Active', 'Deleted') DEFAULT 'Inactive'
            )
        ''')

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Database error:", e)

initialize_database()

# Route: Serve the homepage (index.html)
@app.route('/')
def home():
    return render_template('index.html')

# Route: Admin Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verify the entered password against the stored hash
        if username == ADMIN_USERNAME and ph.verify(ADMIN_PASSWORD_HASH, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid credentials. Try again."

    return render_template('login.html')

# Route: Admin Dashboard
@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    flights = get_all_flights()
    return render_template('admin.html', flights=flights)

# Route: Logout
@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

# Function: Save flight plan into the database
def save_flight_plan(flightnum, aircrafttype, departure, arrival, route, flight_rules):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO flight_plans (flightnum, aircrafttype, departure, arrival, route, flight_rules)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (flightnum, aircrafttype, departure, arrival, route, flight_rules))

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print("Error:", e)
        return False
    
# Route to serve the "File Flight Plan" page (file.html)
@app.route('/file')
def file_flight_plan():
    return render_template('file.html')

@app.route('/rules')
def open_rules():
    return render_template('rules.html')

# Route: Handle flight plan submissions
@app.route('/submit', methods=['POST'])
def submit_flight():
    flightnum = request.form['flightnum']
    aircrafttype = request.form['aircrafttype']
    departure = request.form['departure']
    arrival = request.form['arrival']
    route = request.form['route']
    flight_rules = request.form.get('flight_rules', 'VFR')  # Default to VFR if not selected

    success = save_flight_plan(flightnum, aircrafttype, departure, arrival, route, flight_rules)

    if success:
        return redirect(url_for('home'))
    else:
        return "Error submitting flight plan.", 500

# Function: Retrieve all flight plans (excluding "Deleted")
def get_all_flights():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM flight_plans WHERE status != 'Deleted'")
        flights = cursor.fetchall()

        conn.close()
        return flights
    except Exception as e:
        print("Error fetching flights:", e)
        return []

# Route: Update individual flight status
@app.route('/update_status', methods=['POST'])
def update_status():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    flight_id = request.form['flight_id']
    new_status = request.form['status']

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("UPDATE flight_plans SET status = %s WHERE id = %s", (new_status, flight_id))
        conn.commit()

        cursor.close()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        print("Error updating status:", e)
        return "Error updating flight status.", 500

# Route: Bulk update all flight statuses
@app.route('/update_all_statuses', methods=['POST'])
def update_all_statuses():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        for flight_id, new_status in request.form.items():
            if flight_id.startswith("status_"):  # Ensure valid field
                flight_id_clean = flight_id.replace("status_", "")
                cursor.execute("UPDATE flight_plans SET status = %s WHERE id = %s", (new_status, flight_id_clean))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        print("Error updating all statuses:", e)
        return "Error updating all flight statuses.", 500

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)