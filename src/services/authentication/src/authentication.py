from flask import Flask, request, jsonify, make_response
import psycopg2, os
import jwt

app = Flask(__name__)

USERNAME = 'admin' # change admin for deployment
PASSWORD = 'admin' # change admin for deployment
SECRET = 'secret' # change secret for deployment

#set db connection

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")


def database():
    conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    return conn.cursor()

@app.route('/login', methods=['POST'])
def login():
    
    auth = request.json

    if not auth:
        return jsonify({'message': 'Missing credentials'}), 400

    if auth['username'] != USERNAME or auth['password'] != PASSWORD:
        return jsonify({'message': 'Invalid credentials'}), 401
    
    encoded_jwt = jwt.encode({"id": 1}, SECRET, algorithm="HS256")

    response = make_response(jsonify({'message': 'Login successful'}))

    response.set_cookie('session', encoded_jwt, httponly=True)

    return response





    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)