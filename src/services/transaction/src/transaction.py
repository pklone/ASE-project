from flask import Flask, request, jsonify, abort
from datetime import datetime, timezone
import psycopg2
import psycopg2.extras
import os
import uuid
import re

app = Flask(__name__)

#set db connection
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

UUID_REGEX = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

def check_uuid(uuid_string):
    p = re.compile(UUID_REGEX, re.IGNORECASE)
    m = p.match(uuid_string)

    return m is not None

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

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * from transaction')
        records = cursor.fetchall()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})

    return jsonify({'response': records})

@app.route('/', methods=['POST'])
def create():
    if request.headers.get('Content-Type') != 'application/json':
        return jsonify({'message': 'Content-type not supported'}), 400

    try:
        uuid_player = request.json['uuid_player']
        price = request.json['price']
    except KeyError:
        return jsonify({'message': 'Missing data'}), 400

    if not check_uuid(uuid_player):
        return jsonify({'message': 'Invalid player uuid'}), 400

    created_at = int(datetime.now(tz=timezone.utc).timestamp())
    uuid_transaction = str(uuid.uuid4())

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('INSERT INTO transaction (id, uuid, price, created_at, uuid_player) VALUES (DEFAULT, %s, %s, %s, %s)', 
            [uuid_transaction, price, created_at, uuid_player])
        cursor.execute('SELECT id, uuid, price, created_at, uuid_player FROM transaction WHERE uuid = %s', 
            [uuid_transaction])
        record = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'error': str(e)})

    return jsonify({'response': record})

@app.route('/uuid/<string:transaction_uuid>', methods=['GET'])
def show_by_uuid(transaction_uuid):
    result = {}

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT id, uuid, price, created_at, uuid_player FROM transaction WHERE uuid = %s', 
            [transaction_uuid])
        record = cursor.fetchone()

        if record:
            result = record

        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})

    return jsonify({'response': result})

@app.route('/user/<string:player_uuid>', methods=['GET'])
def show_by_user(player_uuid):        
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT id, uuid, price, created_at FROM transaction WHERE uuid_player = %s', 
            [player_uuid])
        records = cursor.fetchall()

        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})

    return jsonify({'response': records})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)