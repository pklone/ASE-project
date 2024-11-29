from flask import Flask, request, jsonify, make_response, json, render_template
from datetime import datetime, timezone, timedelta
import psycopg2, os
import psycopg2.extras
import jwt
import bcrypt
import requests
import pybreaker

app = Flask(__name__)

circuitbreaker = pybreaker.CircuitBreaker(
    fail_max=5, 
    reset_timeout=60*5
)

#set db connection
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH = os.getenv("KEY_PATH")
POSTGRES_SSLMODE = os.getenv("POSTGRES_SSLMODE")

# set jwt
SECRET = os.getenv("JWT_SECRET")

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({'response': "page not found"}), 404

@app.route('/login', methods=['GET'])
def index():
    return render_template('index.html'), 200

@app.route('/admin_login', methods=['POST'])
def admin_login():
    result = {}
    
    admin_username = request.json.get('username')
    admin_password = request.json.get('password')

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode=POSTGRES_SSLMODE
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM admin WHERE username = %s', 
            [admin_username])
        record = cursor.fetchone()

        if record:
            result = record

        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500
    
    admin = result

    if admin == {} or not bcrypt.checkpw(admin_password.encode(), admin['password_hash'].encode()):
        return jsonify({'response': 'Invalid credentials'}), 401
    
    expire = datetime.now(tz=timezone.utc) + timedelta(seconds=3600)
    payload = {
        'id': admin['id'], 
        'admin': True,
        'exp': expire
    }
    
    encoded_jwt = jwt.encode(payload, SECRET, algorithm='HS256')
    response = make_response(jsonify({'response': 'Logged as admin'}))
    response.set_cookie('session', encoded_jwt, httponly=True, expires=expire)

    return response, 200


@app.route('/login', methods=['POST'])
def login():
    encoded_jwt = request.cookies.get('session')

    if encoded_jwt:
        return jsonify({'response': 'Already logged in'}), 200

    if request.headers.get('Content-Type') != 'application/json':
        return jsonify({'response': 'Content-type not supported'}), 400

    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({'response': 'Missing credentials'}), 400

    try:
        r = circuitbreaker.call(requests.get, f'https://player_service:5000/username/{username}', verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500
    
    try:
        response = json.loads(r.text)
    except json.JSONDecodeError as e:
        return jsonify({'response': 'Json error'}), 500

    player = response['response']

    if player == {} or not bcrypt.checkpw(password.encode(), player['password_hash'].encode()):
        return jsonify({'response': 'Invalid credentials'}), 401

    expire = datetime.now(tz=timezone.utc) + timedelta(seconds=3600)
    payload = {
        'uuid': player['uuid'], 
        'exp': expire
    }

    encoded_jwt = jwt.encode(payload, SECRET, algorithm='HS256')
    response = make_response(jsonify({'response': 'Login successful'}))
    response.set_cookie('session', encoded_jwt, httponly=True, expires=expire)

    return response, 200

@app.route('/logout', methods=['DELETE'])
def logout():
    encoded_jwt = request.cookies.get('session')

    if not encoded_jwt:
        return jsonify({'response': 'Already logged out'}), 200

    response = make_response(jsonify({'response': 'Logout successful'}))
    response.set_cookie('session', '', httponly=True, expires=0)

    return response, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=(CERT_PATH, KEY_PATH))