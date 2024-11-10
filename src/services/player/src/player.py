from flask import Flask, request, jsonify, abort
import psycopg2
import os
import uuid
import bcrypt

app = Flask(__name__)

#set db connection
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({'response': "page not found"}), 404

@app.route('/', methods=['GET'])
def show_all():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor()
        cursor.execute('SELECT id, uuid, username, password_hash, wallet from player')
        records = cursor.fetchall()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})

    return jsonify({'response': records})

@app.route('/uuid/<string:player_uuid>', methods=['GET'])
def show_by_uuid(player_uuid):
    result = {}

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor()
        cursor.execute('SELECT id, uuid, username, wallet FROM player WHERE uuid = %s', 
            [player_uuid])
        record = cursor.fetchone()

        if record:
            result = record

        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})

    return jsonify({'response': result})

@app.route('/username/<string:player_username>', methods=['GET'])
def show_by_username(player_username):
    result = {}

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM player WHERE username = %s', 
            [player_username])
        record = cursor.fetchone()

        if record:
            result = record

        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})

    return jsonify({'response': result})

@app.route('/', methods=['POST'])
def create():
    username = request.json['username']
    password = request.json['password']

    player_uuid = str(uuid.uuid4())
    player_password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    player = {
        'uuid': player_uuid,
        'username': username,
        'password': player_password_hash
    }

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor()
        cursor.execute('INSERT INTO player (id, uuid, username, password_hash) VALUES (DEFAULT, %s, %s, %s)', 
            [player['uuid'], player['username'], player['password']])
        cursor.execute('SELECT id, uuid, username, wallet FROM player WHERE uuid = %s', 
            [player_uuid])
        record = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})

    return jsonify({'response': record})

@app.route('/<string:player_uuid>', methods=['DELETE'])
def remove(player_uuid):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor()
        cursor.execute('DELETE FROM player WHERE uuid = %s', 
            [player_uuid])
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return str(e)

    return jsonify({'response': 'ok!'})

@app.route('/<string:uuid>', methods=['PUT'])
def update():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        
        cursor = conn.cursor()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})

    return jsonify({'response': 'ok!'})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)