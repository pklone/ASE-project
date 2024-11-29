from flask import Flask, request, jsonify, json, abort
from datetime import datetime, timezone
import psycopg2
import psycopg2.extras
import requests
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
CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH = os.getenv("KEY_PATH")
POSTGRES_SSLMODE = os.getenv("POSTGRES_SSLMODE")

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
            port=DB_PORT,
            sslmode=POSTGRES_SSLMODE
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * from transaction')
        records = cursor.fetchall()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    return jsonify({'response': records}), 200

@app.route('/', methods=['POST'])
def create():
    if request.headers.get('Content-Type') != 'application/json':
        return jsonify({'message': 'Content-type not supported'}), 400

    try:
        uuid_player = request.json['uuid_player']
        uuid_auction = request.json['uuid_auction']
        price = request.json['price']
    except KeyError:
        return jsonify({'message': 'Missing data'}), 400

    if not check_uuid(uuid_player) or not check_uuid(uuid_auction):
        return jsonify({'message': 'Invalid uuids'}), 400

    created_at = int(datetime.now(tz=timezone.utc).timestamp())
    uuid_transaction = str(uuid.uuid4())

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
        cursor.execute('INSERT INTO transaction (id, uuid, price, created_at, uuid_player, uuid_auction) VALUES (DEFAULT, %s, %s, %s, %s, %s)', 
            [uuid_transaction, price, created_at, uuid_player, uuid_auction])
        cursor.execute('SELECT id, uuid, price, created_at, uuid_player, uuid_auction FROM transaction WHERE uuid = %s', 
            [uuid_transaction])
        record = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'response': record}), 201

@app.route('/uuid/<string:transaction_uuid>', methods=['GET'])
def show_by_uuid(transaction_uuid):
    result = {}

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
        cursor.execute('SELECT id, uuid, price, created_at, uuid_player, uuid_auction FROM transaction WHERE uuid = %s', 
            [transaction_uuid])
        record = cursor.fetchone()

        if record:
            result = record

        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    return jsonify({'response': result}), 200

@app.route('/user/<string:player_uuid>', methods=['GET'])
def show_all_by_user(player_uuid):
    transactions = []
    transactions_in = []
    transactions_out = []

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
        cursor.execute('SELECT id, uuid, price, created_at, uuid_player, uuid_auction FROM transaction WHERE uuid_player = %s', 
            [player_uuid])
        records = cursor.fetchall()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500
    
    for record in records:
        r = requests.get(url=f"https://market_service:5000/market/{record['uuid_auction']}", headers={'Accept': 'application/json'}, verify=False)
        response = json.loads(r.text)
        if response.get("response"):
            to_player = response['response']['player_uuid']
    
            transaction = {
                'id': record['id'],
                'uuid': record['uuid'],
                'price': record['price'],
                'created_at': record['created_at'],
                'bought': player_uuid,
                'sold': to_player,
                'uuid_auction': record['uuid_auction']
            }
            transactions_out.append(transaction)

    r = requests.get(url=f"https://market_service:5000/market/user/{player_uuid}", verify=False) 
    response = json.loads(r.text)
    if response.get("response"):
        for r in response['response']:
            response_uuid = r['uuid']
    
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
                cursor.execute('SELECT id, uuid, price, created_at, uuid_player, uuid_auction FROM transaction WHERE uuid_auction = %s', 
                    [response_uuid])
                records = cursor.fetchall()
                cursor.close()
                conn.close()
            except psycopg2.Error as e:
                return jsonify({'response': str(e)}), 500

            for record in records:
                r = requests.get(url=f"https://market_service:5000/market/{record['uuid_auction']}", headers={'Accept': 'application/json'}, verify=False)
                if response.get("response"):
                    response = json.loads(r.text)
                    to_player = response['response']['player_uuid']

                transaction = {
                    'id': record['id'],
                    'uuid': record['uuid'],
                    'price': record['price'],
                    'created_at': record['created_at'],
                    'bought': to_player,
                    'sold': record['uuid_player'],
                    'uuid_auction': record['uuid_auction']
                }
                transactions_in.append(transaction)

    transactions = {
        "incoming transactions": transactions_in,
        "outgoing transactions": transactions_out
    }

    return jsonify({'response': transactions}), 200

@app.route('/user/<string:player_uuid>/<string:transaction_uuid>', methods=['GET'])
def show_by_user(player_uuid, transaction_uuid):
    result = {}

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
        cursor.execute('SELECT id, uuid, price, created_at, uuid_player, uuid_auction FROM transaction WHERE uuid_player = %s AND uuid = %s', 
            [player_uuid, transaction_uuid])
        record = cursor.fetchone()

        if record:
            result = record
        
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    return jsonify({'response': record}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=(CERT_PATH, KEY_PATH))