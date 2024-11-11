from flask import Flask, request, jsonify, make_response, json
from datetime import datetime, timezone, timedelta
import psycopg2, os
import jwt
import bcrypt
import requests
import bcrypt

app = Flask(__name__)

SECRET = 'secret' # change secret for deployment

#set db connection
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({'response': "page not found"}), 404

@app.route('/login', methods=['POST'])
def login():
    encoded_jwt = request.cookies.get('session')

    if encoded_jwt:
        return jsonify({'response': 'Already logged in'})

    if request.headers.get('Content-Type') != 'application/json':
        return jsonify({'response': 'Content-type not supported'}), 400

    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({'response': 'Missing credentials'}), 400

    r = requests.get(f'http://player_service:5000/username/{username}')
    
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

    return response

@app.route('/logout', methods=['DELETE'])
def logout():
    encoded_jwt = request.cookies.get('session')

    if not encoded_jwt:
        return jsonify({'response': 'Already logged out'})

    response = make_response(jsonify({'response': 'Logout successful'}))
    response.set_cookie('session', '', httponly=True, expires=0)

    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)