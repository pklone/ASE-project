from flask import Flask, request, jsonify, json
from datetime import datetime, timezone
import psycopg2
import psycopg2.extras
import os
import uuid
import requests
import jwt

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

@app.route('/market', methods=['GET'])
def show_all():
    auctions = []
    gachas = {}
    records = {}
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT id, uuid, base_price, gacha_uuid, user_uuid, expired_at, closed from auction')
        result = cursor.fetchall()
        if result:
            records = result
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})

    r = requests.get(url="http://gacha_service:5000/collection")
    gacha_data = json.loads(r.text)

    gachas = {x['uuid']: x for x in gacha_data}
    
    for record in records:
        r = requests.get(url=f"http://player_service:5000/uuid/{record['user_uuid']}")
        player_username = json.loads(r.text)['response']['username']

        if record['gacha_uuid'] in gachas:
            gacha_info = gachas[record['gacha_uuid']]

        if gacha_info: 
            auction = {
                'auction_uuid': record['uuid'],
                'base_price': record['base_price'],
                'Gacha': gacha_info, 
                'player_username': player_username,
                'expired_at': record['expired_at'],
                'closed': record['closed']
            }

            auctions.append(auction)

            
    return jsonify({'response': auctions})

@app.route('/market/<string:auction_uuid>', methods=['GET'])
def show_one(auction_uuid):
    gachas = {}
    record = {}

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT id, uuid, base_price, gacha_uuid, user_uuid, expired_at, closed from auction where uuid = %s',
                        [auction_uuid])
        result = cursor.fetchone()
        if result:
            record = result
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})

    r = requests.get(url="http://gacha_service:5000/collection")
    gacha_data = json.loads(r.text)

    gachas = {x['uuid']: x for x in gacha_data}

    r = requests.get(url=f"http://player_service:5000/uuid/{record['user_uuid']}")
    player_username = json.loads(r.text)['response']['username']

    if record['gacha_uuid'] in gachas:
        gacha_info = gachas[record['gacha_uuid']]

    if gacha_info: 
        auction = {
            'auction_uuid': record['uuid'],
            'base_price': record['base_price'],
            'Gacha': gacha_info, 
            'player_username': player_username,
            'expired_at': record['expired_at'],
            'closed': record['closed']
        }
            
    return jsonify({'response': auction})


@app.route('/market', methods=['POST'])
def create_auction():
    endoded_jwt = request.cookies.get('session')

    if not endoded_jwt:
        return jsonify({'response': 'You\'re not logged'})
    
    try:
        options = {
            'require': ['exp'],
            'verify_signature': True,
            'verify_exp': True
        }

        decoded_jwt = jwt.decode(endoded_jwt, SECRET, algorithms=['HS256'], options=options)
    except jwt.ExpiredSignatureError:
        return jsonify({'response': 'Expired token'})
    except jwt.InvalidTokenError:
        return jsonify({'response': 'Invalid token'})
    
    if 'uuid' not in decoded_jwt:
        return jsonify({'response': 'Try later'})
    
    player_uuid = decoded_jwt['uuid']
    auction_uuid = str(uuid.uuid4())
    gacha_uuid = request.json.get('gacha_uuid')
    starting_price = request.json.get('starting_price')
    expired_at = int(datetime.now(tz=timezone.utc).timestamp() + 3600*24)

    try: 
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})
    
    r = requests.get(url=f'http://player_service:5000/uuid/{player_uuid}')
    player_id = json.loads(r.text)['response']['id']

    r = requests.get(url=f'http://gacha_service:5000/collection/user/{player_id}')
    player_collection = json.loads(r.text)

    player_gacha = None
    for gacha in player_collection:
        if gacha['uuid'] == gacha_uuid:
            player_gacha = gacha
            break
    
    if not player_gacha or player_gacha['quantity'] < 1:
        return jsonify({'response': 'You don\'t have this gacha'})

    
    try: 
        cursor = conn.cursor()
        cursor.execute('SELECT count(id) as active_auctions FROM auction WHERE user_uuid = %s AND gacha_uuid = %s', 
            [player_uuid, gacha_uuid])
        active_auctions = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})
    
    if player_gacha['quantity'] <= active_auctions:
        return jsonify({'response': f'You have only {player_gacha['quantity']} copies of gacha {player_gacha["name"]}'})
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('INSERT INTO auction (id, uuid, base_price, gacha_uuid, user_uuid, expired_at) VALUES (DEFAULT, %s, %s, %s, %s, %s)', 
            [auction_uuid, starting_price, gacha_uuid, player_uuid, expired_at])
        cursor.execute('SELECT id, uuid, base_price, gacha_uuid, user_uuid, expired_at FROM auction WHERE uuid = %s', 
            [auction_uuid])
        record = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})
    
    return jsonify({'response': record})


@app.route('/market/<string:auction_uuid>/bid', methods=['POST'])
def make_bid(auction_uuid):
    endoded_jwt = request.cookies.get('session')

    if not endoded_jwt:
        return jsonify({'response': 'You\'re not logged'})
    
    try:
        options = {
            'require': ['exp'],
            'verify_signature': True,
            'verify_exp': True
        }

        decoded_jwt = jwt.decode(endoded_jwt, SECRET, algorithms=['HS256'], options=options)
    except jwt.ExpiredSignatureError:
        return jsonify({'response': 'Expired token'})
    except jwt.InvalidTokenError:
        return jsonify({'response': 'Invalid token'})
    
    if 'uuid' not in decoded_jwt:
        return jsonify({'response': 'Try later'})
    
    player_uuid = decoded_jwt['uuid']
    offer = request.json.get('offer')

    try: 
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})
    
    try: 
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('''
            SELECT a.base_price, a.expired_at, a.closed, COALESCE(b.offer, 0) AS offer
                FROM auction a 
                LEFT JOIN bid b ON a.uuid = b.auction_uuid 
                WHERE a.uuid = %s 
                ORDER BY b.offer desc limit 1''',
        [auction_uuid])
        record = cursor.fetchone()
        conn.commit()
        cursor.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})
    
    current_time = int(datetime.now(tz=timezone.utc).timestamp())

    final_time = int(record['expired_at'].timestamp())
    base_price = record['base_price']
    current_price = record['offer']

    if final_time <= current_time:
        return jsonify({'response': 'Auction is closed'})
    
    if offer <= base_price:
        return jsonify({'response': 'Offer must be higher than base price'})
    
    if offer <= current_price:
        return jsonify({'response': 'Offer must be higher than current price'})
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT uuid FROM auction WHERE uuid = %s',
            [auction_uuid])
        if cursor.rowcount == 0:
            return jsonify({'response': 'Auction not found'})
        cursor.execute('INSERT INTO bid (id, auction_uuid, user_uuid, offer) VALUES (DEFAULT, %s, %s, %s)', 
            [auction_uuid, player_uuid, offer])
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})
    
    return jsonify({'response': {'auction_uuid': auction_uuid, 'player_uuid': player_uuid, 'offer': offer, 'closed': record['closed']}})

@app.route('/market/<string:auction_uuid>/close', methods=['POST'])
def close_auction(auction_uuid):
    endoded_jwt = request.cookies.get('session')

    if not endoded_jwt:
        return jsonify({'response': 'You\'re not logged'})
    
    try:
        options = {
            'require': ['exp'],
            'verify_signature': True,
            'verify_exp': True
        }

        decoded_jwt = jwt.decode(endoded_jwt, SECRET, algorithms=['HS256'], options=options)
    except jwt.ExpiredSignatureError:
        return jsonify({'response': 'Expired token'})
    except jwt.InvalidTokenError:
        return jsonify({'response': 'Invalid token'})
    
    if 'uuid' not in decoded_jwt:
        return jsonify({'response': 'Try later - jwt error'})
    
    player_uuid = decoded_jwt['uuid'] 

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})
    
    try: 
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('''
            SELECT a.base_price, a.user_uuid, a.expired_at, a.closed, COALESCE(b.offer, 0) AS offer
                FROM auction a 
                LEFT JOIN bid b ON a.uuid = b.auction_uuid 
                WHERE a.uuid = %s 
                ORDER BY b.offer desc limit 1''',
        [auction_uuid])
        record = cursor.fetchone()
        conn.commit()
        cursor.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})
    
    if record['user_uuid'] != player_uuid:
        return jsonify({'response': 'You\'re not the owner of this auction'})
     
    if record['closed'] == True:
        return jsonify({'response': 'Auction is already closed'})
    
    if record['offer'] == 0:
        return jsonify({'response': 'There are no bids for this auction'})
    
    try: 
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('DELETE FROM bid WHERE auction_uuid = %s',
            [auction_uuid])
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})

    try: 
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('UPDATE auction SET closed = TRUE WHERE uuid = %s',
            [auction_uuid])
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})
    
    data = {
        'price': record['offer'],
        'uuid_player': player_uuid,
        'uuid_auction': auction_uuid
    }
    
    r = requests.post(url='http://transaction_service:5000/', json=data)
    if r.status_code != 200:
        return jsonify({'response': 'Try later - transaction error'})

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'response': 'Auction closed'})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)