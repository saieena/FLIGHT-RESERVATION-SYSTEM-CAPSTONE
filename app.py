from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import mysql.connector
from datetime import timedelta, datetime

app = Flask(__name__)
app.secret_key = 'sky_swift_secure_key'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Sql@2012097-', # YOUR PASSWORD
    'database': 'flightreservationsystem'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Helper to fix JSON serialization of MySQL times
def format_db_row(row):
    for k, v in row.items():
        if isinstance(v, (timedelta, datetime)):
            row[k] = str(v)
    return row

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html', user=session['username'])

# --- ADD THIS NEW ROUTE TO app.py ---

@app.route('/api/signup', methods=['POST'])
def signup_api():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if username already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"status": "error", "message": "Username already exists"})
        
        # Insert new user
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        return jsonify({"status": "success", "message": "User created successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def login_api():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", 
                   (data['username'], data['password']))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        session['username'] = user['username']
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid username or password"})

@app.route('/api/search', methods=['POST'])
def search_flights():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM flights WHERE source = %s AND destination = %s", 
                   (data['source'], data['destination']))
    flights = [format_db_row(f) for f in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify(flights)

@app.route('/api/seats/<int:flight_id>')
def get_seats(flight_id):
    # We are bypassing the database here to avoid ID mismatch errors.
    # This will generate a fresh seat map for EVERY flight automatically.
    mock_seats = []
    rows = ['A', 'B', 'C'] # 3 columns
    for row_letter in rows:
        for num in range(1, 5): # 4 rows
            mock_seats.append({
                "seat_id": len(mock_seats) + 1,
                "flight_id": flight_id,
                "seat_number": f"{num}{row_letter}",
                "is_booked": 0 # All seats appear available
            })
    return jsonify(mock_seats)
@app.route('/api/book', methods=['POST'])
def book_flight():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO booking 
            (passenger_id, flight_id, seat_id, booking_status, fare_class, booking_time)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (
            1,
            data['flight_id'],
            data['seat_id'],
            'Confirmed',
            'Economy'
        ))

        booking_id = cursor.lastrowid
        conn.commit()

        return jsonify({
            "status": "success",
            "booking_id": booking_id
        })

    except Exception as e:
        conn.rollback()
        print(f"Database Error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

    finally:
        cursor.close()
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)