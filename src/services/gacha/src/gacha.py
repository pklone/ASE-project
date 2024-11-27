from flask import Flask, request, jsonify, json, render_template
import psycopg2
import psycopg2.extras
import os
import jwt
import random
import requests
import uuid
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './static/images/gachas'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
STATIC_DIR_PATH = '/assets'
GACHAS_DIR_PATH = STATIC_DIR_PATH + '/images/gachas'

app = Flask(__name__, static_url_path=STATIC_DIR_PATH)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000  # 16 MB


DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH = os.getenv("KEY_PATH")

# set jwt
SECRET = os.getenv("JWT_SECRET")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        return jsonify({'response': str(e)}), 500

    if 'application/json' in request.headers['Accept']:
        return jsonify(records), 200
    elif 'text/html' in request.headers['Accept']:
        return render_template('collection.html', records=records), 200
    else:
        return jsonify({'response': 'Not supported'}), 400

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
        return jsonify({'response': str(e)}), 500

    return jsonify(result), 200

@app.route('/collection/user/<string:player_uuid>', methods=['GET'])
def show_by_player(player_uuid):
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
            WHERE pg.uuid_player = %s""", 
        [player_uuid])
        records = cursor.fetchall()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    return jsonify(records), 200

@app.route('/collection/user/<string:player_uuid>', methods=['PUT'])
def update_quantity(player_uuid): # q is 1 (buyer) or -1 (owner)
    q = request.json.get('q')
    uuid_gacha = request.json.get('gacha_uuid')

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM player_gacha WHERE uuid_player = %s AND id_gacha = (SELECT id FROM gacha WHERE uuid = %s)', 
            [player_uuid, uuid_gacha])

        if cursor.rowcount == 0:
            cursor.execute('INSERT INTO player_gacha (uuid_player, id_gacha) VALUES (%s, (SELECT id FROM gacha WHERE uuid = %s))',
                [player_uuid, uuid_gacha])
        else:
            cursor.execute('UPDATE player_gacha SET quantity = quantity + (%s) WHERE uuid_player = %s AND id_gacha = (SELECT id FROM gacha WHERE uuid = %s)', 
                [q, player_uuid, uuid_gacha])
        
        conn.commit()
        cursor.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500
    
    return jsonify({'response': 'success'}), 200

@app.route('/roll', methods=['GET'])
def roll():
    encoded_jwt = request.cookies.get('session')

    if not encoded_jwt:
        return jsonify({'response': 'You\'re not logged'}), 401

    try:
        options = {
            'require': ['exp'], 
            'verify_signature': True, 
            'verify_exp': True
        }

        decoded_jwt = jwt.decode(encoded_jwt, SECRET, algorithms=['HS256'], options=options)
    except jwt.ExpiredSignatureError:
        return jsonify({'response': 'Expired token'}), 403
    except jwt.InvalidTokenError:
        return jsonify({'response': 'Invalid token'}), 403

    if 'uuid' not in decoded_jwt:
        return jsonify({'response': 'Try later'}), 403

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
        return jsonify({'response': str(e)}), 500

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
        return jsonify({'response': str(e)}), 500

    gacha_id = random.choice(records)[0]

    data = {
        'player_uuid': player_uuid,
        'purchase': -10
    }

    r = requests.post(url='https://player_service:5000/currency/buy', verify=False, json=data)
    if r.status_code != 200:
        return jsonify({'response': 'Try later'}), 500

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM player_gacha WHERE uuid_player = %s AND id_gacha = %s",
            [player_uuid, gacha_id])

        if cursor.rowcount == 0:
            cursor.execute("INSERT INTO player_gacha (uuid_player, id_gacha) VALUES (%s, %s)", 
                [player_uuid, gacha_id])
        else:
            cursor.execute("UPDATE player_gacha SET quantity = quantity + 1 WHERE uuid_player = %s AND id_gacha = %s", 
                [player_uuid, gacha_id])
            
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
        return jsonify({'response': str(e)}), 500

    return jsonify({'response': record}), 200

@app.route('/collection', methods=['POST'])
def add_gacha():
    if 'gacha_image' not in request.files:
        return {'response': 'gacha image not found'}, 400

    file = request.files['gacha_image']
    if file.filename == '':
        return {'response': 'filename not found'}, 400

    if not file or not allowed_file(file.filename):
        return {'response': 'invalid image format or empty image'}, 400
    
    try:
        new_name = request.form['name']
        new_description = request.form['description']
        new_rarity = request.form['new_rarity']
    except KeyError:
        return {'response': 'Missing data'}, 400

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT id from Rarity where symbol = %s', [new_rarity])
        
        if cursor.rowcount == 0:
            return {'response': 'invalid rarity'}, 400

        record = cursor.fetchone()
        rarity_id = record['id']
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    try:
        filename = secure_filename(file.filename)
        destination_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(destination_path)
    except FileNotFoundError:
        return {'response': 'Internal error'}, 500

    new_uuid = str(uuid.uuid4())
    new_image_path = os.path.join(GACHAS_DIR_PATH, filename)

    try:
        cursor.execute("""
            INSERT INTO gacha (id, uuid, name, description, image_path, id_rarity) 
            VALUES (DEFAULT, %s, %s, %s, %s, %s)""", 
            (new_uuid, new_name, new_description, new_image_path, rarity_id))
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500
    
    return jsonify({'response': 'Gacha added'}), 201
    
@app.route('/collection/<string:gacha_uuid>', methods=['PUT'])
def modify_gacha(gacha_uuid):
    new_name = request.form.get('name')
    new_description = request.form.get('description')
    new_rarity = request.form.get('new_rarity')
    
    new_image_path = None
    rarity_id = None

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    if new_rarity:
        try:
            cursor.execute('SELECT id from Rarity where symbol = %s', [new_rarity])
            
            if cursor.rowcount == 0:
                return {'response': 'invalid rarity'}, 400

            record = cursor.fetchone()
            rarity_id = record['id']
        except psycopg2.Error as e:
            return jsonify({'response': str(e)}), 500
    
    if 'gacha_image' in request.files:
        file = request.files['gacha_image']

        if file.filename == '':
            return {'response': 'gacha image filename not found'}, 400

        if not file or not allowed_file(file.filename):
            return {'response': 'invalid image format or empty image'}, 400
        
        try:
            filename = secure_filename(file.filename)
            destination_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(destination_path)
            new_image_path = os.path.join(GACHAS_DIR_PATH, filename)
        except FileNotFoundError:
            return {'response': 'Internal error'}, 500

    try:
        cursor.execute("""
            UPDATE gacha SET
                name = COALESCE(%s, name),
                description = COALESCE(%s, description),
                image_path = COALESCE(%s, image_path),
                id_rarity = COALESCE(%s, id_rarity)
            WHERE uuid = %s""", [new_name, new_description, new_image_path, rarity_id, gacha_uuid])

        if cursor.rowcount == 0:
            return jsonify({'response': 'Query as not updated nothing'}), 404

        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500
    
    return jsonify({'response': 'Gacha updated'}), 200

@app.route('/collection/<string:gacha_uuid>', methods=['DELETE'])
def delete_gacha(gacha_uuid):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("DELETE FROM gacha WHERE uuid = %s", [gacha_uuid])
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500
    
    return jsonify({'response': 'Gacha deleted'}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=(CERT_PATH, KEY_PATH))