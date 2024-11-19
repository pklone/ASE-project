from flask import Flask, request, jsonify, json
import psycopg2
import psycopg2.extras
import os
import jwt
import random
import requests
import uuid

app = Flask(__name__, static_url_path='/assets')

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

@app.route('/collection', methods=['GET'])
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
        cursor.execute("""
            SELECT g.id, uuid, g.name, description, image_path, r.name as rarity 
            FROM gacha g 
                INNER JOIN rarity r on g.id_rarity = r.id""")
        records = cursor.fetchall()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return str(e)

    return jsonify(records)

@app.route('/collection/<string:gacha_uuid>', methods=['GET'])
def show(gacha_uuid):
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
        cursor.execute("SELECT * FROM gacha WHERE uuid = %s", [gacha_uuid])
        record = cursor.fetchone()

        if record:
            result = record

        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return str(e)

    return jsonify(result)

@app.route('/collection/user/<int:player_id>', methods=['GET'])
def show_by_player(player_id):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT g.id, uuid, g.name, description, image_path, quantity, r.name as rarity 
            FROM gacha g 
                INNER JOIN rarity r on g.id_rarity = r.id 
                INNER JOIN player_gacha pg on g.id = pg.id_gacha 
            WHERE pg.id_player = %s""", 
        [player_id])
        records = cursor.fetchall()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return str(e)

    return jsonify(records)

@app.route('/collection/user/<int:player_uuid>', methods=['PUT'])
def update_quantity(player_uuid, gacha_uuid, q): # q is 1 (buyer) or -1 (owner)
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    except psycopg2.Error as e:
        return str(e)

    r = requests.get(url=f'http://player_service:5000/uuid/{player_uuid}')
    response = json.loads(r.text)

    try: 
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT 1 FROM player_gacha WHERE id = %s', [response['response']['id']])
        if cursor.rowcount == 0:
            cursor.execute('INSERT INTO player_gacha (id_player, id_gacha) VALUES (%s, (SELECT id FROM gacha WHERE uuid = %s))',
                [response['response']['id'], gacha_uuid])
        else:
            record = cursor.fetchone()
            cursor.execute('UPDATE player_gacha SET quantity = quantity + %s WHERE id = %s', [q, record['id']])
        conn.commit()
        cursor.close()
    except psycopg2.Error as e:
        return str(e)
    
    return jsonify({'response': 'success'})


@app.route('/roll', methods=['GET'])
def roll():
    encoded_jwt = request.cookies.get('session')

    if not encoded_jwt:
        return jsonify({'response': 'You\'re not logged'})

    try:
        options = {
            'require': ['exp'], 
            'verify_signature': True, 
            'verify_exp': True
        }

        decoded_jwt = jwt.decode(encoded_jwt, SECRET, algorithms=['HS256'], options=options)
    except jwt.ExpiredSignatureError:
        return jsonify({'response': 'Expired token'})
    except jwt.InvalidTokenError:
        return jsonify({'response': 'Invalid token'})

    if 'uuid' not in decoded_jwt:
        return jsonify({'response': 'Try later'})

    player_uuid = decoded_jwt['uuid']

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT id, percentage FROM rarity')
        records = cursor.fetchall()
        cursor.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})

    percentages = [x['percentage'] for x in records]
    weights = [x['id'] for x in records]

    rarity_id = random.choices(weights, percentages)[0]

    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM gacha WHERE id_rarity = %s',
            [rarity_id])
        records = cursor.fetchall()
        cursor.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})

    gacha_id = random.choice(records)[0]

    data = {
        'player_uuid': player_uuid,
        'purchase': -10
    }

    r = requests.post(url='http://player_service:5000/currency/buy', json=data)
    if r.status_code != 200:
        return jsonify({'response': 'Try later'})

    r = requests.get(url=f'http://player_service:5000/uuid/{player_uuid}')
    response = json.loads(r.text)
    player = response['response']

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM player_gacha WHERE id_player = %s AND id_gacha = %s",
            [player['id'], gacha_id])

        if cursor.rowcount == 0:
            cursor.execute("INSERT INTO player_gacha (id_player, id_gacha) VALUES (%s, %s)", 
                [player['id'], gacha_id])
        else:
            cursor.execute("UPDATE player_gacha SET quantity = quantity + 1 WHERE id_player = %s AND id_gacha = %s", 
                [player['id'], gacha_id])
            
        cursor.execute("""
            SELECT uuid, g.name, description, image_path, r.name as rarity 
            FROM gacha g 
                INNER JOIN rarity r ON g.id_rarity = r.id 
            WHERE g.id = %s""", 
                [gacha_id])
        record = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})

    return jsonify({'response': record})

@app.route('/collection', methods=['POST'])
def add_gacha():
    new_uuid = str(uuid.uuid4())
    new_name = request.json.get('name')
    new_description = request.json.get('description')
    new_image_path = request.json.get('image_path')
    new_rarity = request.json.get('new_rarity')

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            INSERT INTO gacha (id, uuid, name, description, image_path, id_rarity) 
            VALUES (DEFAULT, %s, %s, %s, %s, %s)""", 
            (new_uuid, new_name, new_description, new_image_path, new_rarity))
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})
    
    return jsonify({'response': 'Gacha added'}), 200
    
@app.route('/collection/<string:gacha_uuid>', methods=['PUT'])
def modify_gacha(gacha_uuid):
    new_name = request.json.get('new_name')
    new_description = request.json.get('new_description')
    new_image_path = request.json.get('new_image_path')
    new_rarity = request.json.get('new_rarity')
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
        UPDATE gacha
        SET
        name = COALESCE(%s, name),
        description = COALESCE(%s, description),
        image_path = COALESCE(%s, image_path),
        id_rarity = COALESCE(%s, id_rarity)
        WHERE uuid = %s;
        """, (new_name, new_description, new_image_path, new_rarity, gacha_uuid))
        if cursor.rowcount == 0:
            return jsonify({'response': 'Query as not updated nothing'}), 404
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})
    
    return jsonify({'response': 'Gacha updated'})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)