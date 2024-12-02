from flask import Flask, request, jsonify, abort
import psycopg2
import psycopg2.extras
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
CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH = os.getenv("KEY_PATH")
POSTGRES_SSLMODE = os.getenv("POSTGRES_SSLMODE")

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

        cursor = conn.cursor()
        cursor.execute('SELECT id, uuid, username, password_hash, wallet from player')
        records = cursor.fetchall()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    return jsonify({'response': records}), 200

@app.route('/id/<int:player_id>', methods=['GET'])
def show_by_id(player_id):
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
        cursor.execute('SELECT id, uuid, username, wallet FROM player WHERE id = %s', 
            [player_id])
        record = cursor.fetchone()

        if record:
            result = record

        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    return jsonify({'response': result}), 200

@app.route('/uuid/<string:player_uuid>', methods=['GET'])
def show_by_uuid(player_uuid):
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
        cursor.execute('SELECT id, uuid, username, wallet FROM player WHERE uuid = %s', 
            [player_uuid])
        record = cursor.fetchone()

        if record:
            result = record

        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    return jsonify({'response': result}), 200

@app.route('/uuid/<string:player_uuid>', methods=['PUT'])
def modify_by_uuid(player_uuid):
    result = {}

    new_username = request.json.get('username')
    new_wallet = request.json.get('wallet')

    new_player = {
        'username': new_username,
        'wallet': new_wallet
    }

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
        cursor.execute("""
        UPDATE player
        SET
        username = COALESCE(%s, username),
        wallet = COALESCE(%s, wallet)
        WHERE uuid = %s;
        """, (new_player['username'], new_player['wallet'], player_uuid))
        if cursor.rowcount == 0:
            return jsonify({'response': 'Query as not updated nothing'}), 404
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    return jsonify({'response': "User updated Successfully!"}), 200

@app.route('/username/<string:player_username>', methods=['GET'])
def show_by_username(player_username):
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
        cursor.execute('SELECT * FROM player WHERE username = %s', 
            [player_username])
        record = cursor.fetchone()

        if record:
            result = record

        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    return jsonify({'response': result}), 200

@app.route('/', methods=['POST'])
def create():
    if request.headers.get('Content-Type') != 'application/json':
        return jsonify({'message': 'Content-type not supported'}), 400

    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({'response': 'Missing data'}), 400

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
            port=DB_PORT,
            sslmode=POSTGRES_SSLMODE
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
        return jsonify({'response': str(e)}), 500

    return jsonify({'response': record}), 201

@app.route('/id/<int:player_id>', methods=['DELETE'])
def remove_by_id(player_id):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode=POSTGRES_SSLMODE
        )

        cursor = conn.cursor()
        cursor.execute('DELETE FROM player WHERE id = %s', 
            [player_id])
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    return jsonify({'response': 'ok!'}), 200

@app.route('/uuid/<string:player_uuid>', methods=['DELETE'])
def remove_by_uuid(player_uuid):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode=POSTGRES_SSLMODE
        )

        cursor = conn.cursor()
        cursor.execute('DELETE FROM player WHERE uuid = %s', 
            [player_uuid])
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    return jsonify({'response': 'ok!'}), 200

@app.route('/<string:uuid>/wallet', methods=['PUT'])
def update_wallet(uuid):
    amount = request.json['amount']
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode=POSTGRES_SSLMODE
        )
        
        cursor = conn.cursor()
        cursor.execute('UPDATE player SET wallet = wallet + %s WHERE uuid = %s', [amount, uuid])
        if cursor.rowcount == 0:
            return jsonify({'response': 'Query as not updated nothing'}), 404
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    return jsonify({'response': "wallet updated Successfully!"}), 200

@app.route('/currency/buy', methods=['POST'])
def currency():
    player_uuid = request.json['player_uuid']
    purchase = request.json['purchase']

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode=POSTGRES_SSLMODE
        )
        
        cursor = conn.cursor()
        cursor.execute('UPDATE player SET wallet = wallet + %s WHERE uuid = %s', [purchase, player_uuid])
        if cursor.rowcount == 0:
            return jsonify({'response': 'Query as not updated nothing'}), 404
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    return jsonify({'response': "wallet updated Successfully!"}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=(CERT_PATH, KEY_PATH))