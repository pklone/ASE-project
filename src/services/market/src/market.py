from flask import Flask, request, jsonify, json, render_template
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from functools import wraps
import socket
import psycopg2
import psycopg2.extras
import os
import uuid
import requests
import jwt
import pybreaker
from mytasks import add, req, invoke_payment

#Controllare la close della connection al db ogni volta

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

def login_required(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
      encoded_jwt = request.headers.get('Authorization')
  
      if not encoded_jwt:
          return jsonify({'response': 'You\'re not logged'}), 401
      
      encoded_jwt = encoded_jwt.split(' ')[1]
  
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
  
      if 'sub' not in decoded_jwt:
          return jsonify({'response': 'Try later'}), 403
      
      if decoded_jwt['scope'] != 'player':
          return jsonify({'response': 'You are not autorized'}), 401 
  
      additional = {'auth_uuid': decoded_jwt['sub']}
  
      return f(*args, **kwargs, **additional)
  
  return decorated_function

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({'response': "page not found"}), 404

@app.route('/market', methods=['GET'])
def show_all():
    auctions = []
    gachas = {}
    records = {}

    is_admin = False

    try:
        hostname = (socket.gethostbyaddr(request.remote_addr)[0]).split('.')[0]    
    except socket.herror:
        return {'response': 'unknown host'}, 500

    if hostname == 'admin_service':
        is_admin = True

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
        cursor.execute('''SELECT id, uuid, base_price, gacha_uuid, user_uuid, to_char(expired_at, 'DD/MM/YYYY HH:MI:SSOF:00') as expired_at, closed from auction''')
        result = cursor.fetchall()
        if result:
            records = result
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    try:
        r = circuitbreaker.call(requests.get, 'https://gacha_service:5000/collection', verify=False, headers={'Accept': 'application/json'})
    except Exception as e:
        return jsonify({'response': str(e)}), 500

    if r.status_code != 200:
        return jsonify({'response': 'Try later - gacha service error'}), 500
    gacha_data = json.loads(r.text)['response']

    gachas = {x['uuid']: x for x in gacha_data}
    
    for record in records:
        try:
            r = circuitbreaker.call(requests.get, f'https://player_service:5000/uuid/{record["user_uuid"]}', verify=False, headers={'Accept': 'application/json'})
        except Exception as e:
            return jsonify({'response': str(e)}), 500
        if r.status_code != 200:   
            return jsonify({'response': 'Try later - player service error'}), 500
        player_username = json.loads(r.text)['response']['username']

        if record['gacha_uuid'] in gachas:
            gacha_info = gachas[record['gacha_uuid']]

        if gacha_info: 
            expire_utc = datetime.strptime(record['expired_at'], '%d/%m/%Y %H:%M:%S%z')
            expire = expire_utc.astimezone(ZoneInfo('Europe/Rome'))

            auction = {
                'auction_uuid': record['uuid'],
                'base_price': record['base_price'],
                'Gacha': gacha_info, 
                'player_username': player_username,
                'user_uuid': record['user_uuid'],
                'expired_at': expire.strftime('%d/%m/%Y %H:%M:%S %Z'),
                'closed': record['closed']
            }
            
            if not is_admin:
                if record['closed'] == True:
                    continue
                else:
                    auctions.append(auction)
            else:
                auctions.append(auction)

    if 'application/json' in request.headers.get('Accept'):
        return jsonify({'response': auctions}), 200
    elif 'text/html' in request.headers.get('Accept'):
        return render_template("marketplace.html", auctions=auctions), 200
    else:
        return jsonify({'response': 'Not supported'}), 400

@app.route('/market/<string:auction_uuid>', methods=['GET'])
def show_one(auction_uuid):
    gachas = {}
    record = {}

    is_admin = False
    hostname = (socket.gethostbyaddr(request.remote_addr)[0]).split('.')[0]
    if hostname == 'admin_service' or hostname == 'transaction_service': #TODO controllare se transaction service funge
        is_admin = True

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
        cursor.execute('''
            SELECT a.uuid, a.base_price, a.gacha_uuid, a.user_uuid, a.expired_at, a.closed, COALESCE(b.offer, 0) AS offer
                FROM auction a 
                LEFT JOIN bid b ON a.uuid = b.auction_uuid 
                WHERE a.uuid = %s 
                ORDER BY b.offer desc limit 1''',
        [auction_uuid])
        record = cursor.fetchone()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})
    
    try:
        r = circuitbreaker.call(requests.get, 'https://gacha_service:5000/collection', verify=False , headers={'Accept': 'application/json'})

        gacha_data = json.loads(r.text)['response']
        gachas = {x['uuid']: x for x in gacha_data}

        r = circuitbreaker.call(requests.get, f'https://player_service:5000/uuid/{record["user_uuid"]}', verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500
    if r.status_code != 200:
        return jsonify({'response': 'Try later - player service error'}), 500
    
    player_username = json.loads(r.text)['response']['username']

    if record['gacha_uuid'] in gachas:
        gacha_info = gachas[record['gacha_uuid']]

    if gacha_info: 
        auction = {
            'auction_uuid': record['uuid'],
            'base_price': record['base_price'],
            'Gacha': gacha_info, 
            'player_username': player_username,
            'player_uuid': record['user_uuid'],
            'expired_at': record['expired_at'],
            'closed': record['closed'],
            'actual_offer': record['offer']
        }

    if not is_admin and record['closed'] == True:
        return jsonify({'response': 'Auction is closed'}), 200 
            
    if 'application/json' in request.headers.get('Accept'):
        return jsonify({'response': auction}), 200
    elif 'text/html' in request.headers.get('Accept'):
        return render_template("auction_details.html", auction=auction), 200
    else:
        return jsonify({'response': 'Not supported'}), 400
    
@app.route('/market/gacha/<string:gacha_uuid>', methods=['GET'])
def show_create_auction(gacha_uuid):
    return render_template("create_auction.html", gacha_uuid=gacha_uuid), 200

@app.route('/market', methods=['POST'])
@login_required
def create_auction(auth_uuid):
    auction_uuid = str(uuid.uuid4())
    if request.is_json: 
       gacha_uuid = request.json.get('gacha_uuid')
       starting_price = request.json.get('starting_price')
    else:  
       gacha_uuid = request.form.get('gacha_uuid')
       starting_price = request.form.get('starting_price')

    if not gacha_uuid or not starting_price:
        return jsonify({'response': 'Missing gacha_uuid or starting_price'}), 400
    expired_at = datetime.now(tz=timezone.utc) + timedelta(seconds=60*5)

    if int(starting_price) <= 0:
        return jsonify({'response': 'Starting price must be positive'}), 400

    try: 
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode=POSTGRES_SSLMODE
        )

        r = circuitbreaker.call(requests.get, f'https://gacha_service:5000/collection/user/{auth_uuid}', verify=False)
        if r.status_code != 200:
            return jsonify({'response': 'Try later - gacha service error'}), 500
    except Exception as e:
        return jsonify({'response': str(e)}), 500
    except psycopg2.Error as e:
        return jsonify({'response': str(e)})
    
    player_collection = json.loads(r.text)['response']

    player_gacha = None
    for gacha in player_collection:
        if gacha['uuid'] == gacha_uuid:
            player_gacha = gacha
            break
    
    if not player_gacha or player_gacha['quantity'] < 1:
        return jsonify({'response': 'You don\'t have this gacha'}), 400
    
    try: 
        cursor = conn.cursor()
        cursor.execute('SELECT count(id) as active_auctions FROM auction WHERE user_uuid = %s AND gacha_uuid = %s', 
            [auth_uuid, gacha_uuid])
        active_auctions = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500
    
    if player_gacha['quantity'] <= active_auctions:
        return jsonify({'response': f'You have only {player_gacha['quantity']} copies of gacha {player_gacha["name"]}'}), 400
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('INSERT INTO auction (id, uuid, base_price, gacha_uuid, user_uuid, expired_at) VALUES (DEFAULT, %s, %s, %s, %s, %s)', 
            [auction_uuid, starting_price, gacha_uuid, auth_uuid, expired_at])
        cursor.execute('SELECT id, uuid, base_price, gacha_uuid, user_uuid, expired_at FROM auction WHERE uuid = %s', 
            [auction_uuid])
        record = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500

    task = invoke_payment.apply_async((auction_uuid,), eta=expired_at)
    
    if 'application/json' in request.headers.get('Accept'):
        return jsonify({'response': record}), 201
    elif 'text/html' in request.headers.get('Accept'):
        return render_template("create_auction.html", success=True), 201
    else:
        return jsonify({'response': 'Not supported'}), 400

@app.route('/market/<string:auction_uuid>/bid', methods=['POST'])
@login_required
def make_bid(auction_uuid, auth_uuid):
    if request.is_json: 
       offer = request.json.get('offer')
    else:  
       offer = request.form.get('offer')

    offer = int(offer)
    
    if int(offer) <= 0:
        return jsonify({'response': 'Bid must be positive'}), 400

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
        cursor.execute('''
            SELECT a.base_price, a.expired_at, a.closed, a.user_uuid, COALESCE(b.offer, 0) AS offer
                FROM auction a 
                LEFT JOIN bid b ON a.uuid = b.auction_uuid 
                WHERE a.uuid = %s 
                ORDER BY b.offer desc limit 1''',
        [auction_uuid])
        record = cursor.fetchone()
        conn.commit()
        cursor.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500
    
    current_time = int(datetime.now(tz=timezone.utc).timestamp())
    final_time = int(record['expired_at'].timestamp())
    base_price = record['base_price']
    current_price = record['offer']

    if auth_uuid == record['user_uuid']:
        return jsonify({'response': 'You\'re the owner of this auction'}), 400

    if final_time <= current_time:
        return jsonify({'response': 'Auction is closed'}), 400
    
    if offer <= base_price:
        return jsonify({'response': 'Offer must be higher than base price'}), 400
    
    if offer <= current_price:
        return jsonify({'response': 'Offer must be higher than current price'}), 400
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT uuid FROM auction WHERE uuid = %s',
            [auction_uuid])
        if cursor.rowcount == 0:
            return jsonify({'response': 'Auction not found'})
        cursor.execute('INSERT INTO bid (id, auction_uuid, user_uuid, offer) VALUES (DEFAULT, %s, %s, %s)', 
            [auction_uuid, auth_uuid, offer])
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500
    
    return jsonify({'response': {'auction_uuid': auction_uuid, 'player_uuid': auth_uuid, 'offer': offer, 'closed': record['closed']}}), 200

@app.route('/market/<string:auction_uuid>/close', methods=['PUT'])
def close_auction(auction_uuid):
    
    player_uuid = None
    is_admin = False

    hostname = (socket.gethostbyaddr(request.remote_addr)[0]).split('.')[0]

    if hostname == 'admin_service':
        is_admin = True

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
        cursor.execute('''
            SELECT a.user_uuid, a.closed, COALESCE(b.offer, 0) AS offer
                FROM auction a 
                LEFT JOIN bid b ON a.uuid = b.auction_uuid 
                WHERE a.uuid = %s 
                ORDER BY b.offer desc limit 1''',
        [auction_uuid])
        
        if cursor.rowcount == 0:
            return {'response': 'Auction not found'}, 400
        
        record = cursor.fetchone()
        conn.commit()
        cursor.close()
    except psycopg2.Error as e:
        return {'response': str(e)}, 500
    
    if not is_admin:
        endoded_jwt = request.headers.get('Authorization')

        if not endoded_jwt:
            return jsonify({'response': 'You\'re not logged'}), 401

        try:
            options = {
                'require': ['exp'],
                'verify_signature': True,
                'verify_exp': True
            }

            decoded_jwt = jwt.decode(endoded_jwt, SECRET, algorithms=['HS256'], options=options)
        except jwt.ExpiredSignatureError:
            return jsonify({'response': 'Expired token'}), 403

        if 'sub' not in decoded_jwt:
            return jsonify({'response': 'Try later - jwt error'}), 403

        player_uuid = decoded_jwt['sub']

        if record['user_uuid'] != player_uuid:
            return jsonify({'response': 'You\'re not the owner of this auction'}), 400
        if record['offer'] != 0:
            return {'response': 'Not possible to close auction with bids'}, 400

    if record['closed'] == True:
        return {'response': 'Auction is already closed'}, 400
    try: 
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('DELETE FROM bid WHERE auction_uuid = %s',
            [auction_uuid])
        cursor.execute('UPDATE auction SET closed = TRUE WHERE uuid = %s',
            [auction_uuid])
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return {'response': str(e)}, 500
    return {'response': 'Auction closed'}, 200

@app.route('/market/<string:auction_uuid>/payment', methods=['POST'])
def payment(auction_uuid):
    hostname = (socket.gethostbyaddr(request.remote_addr)[0]).split('.')[0]
    
    if 'celery_worker' not in hostname and 'admin_service' not in hostname:
        return jsonify({'response': 'You\'re not authorized'}), 403

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode=POSTGRES_SSLMODE
        )
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500
    
    try: 
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('''
            WITH RankedBids AS (
                SELECT 
                    a.user_uuid AS owner, 
                    a.gacha_uuid,
                    a.closed,
                    b.user_uuid AS buyer, 
                    COALESCE(b.offer, 0) AS offer
                FROM auction a
                LEFT JOIN bid b ON a.uuid = b.auction_uuid
                WHERE a.uuid = %s
                ),
            DistinctBuyers AS (
                SELECT DISTINCT ON (buyer) 
                    owner, 
                    buyer, 
                    gacha_uuid,
                    closed,
                    offer
                FROM RankedBids
                WHERE buyer IS NOT NULL
                ORDER BY buyer, offer DESC
                )
            SELECT owner, buyer, closed, gacha_uuid, offer
            FROM DistinctBuyers
            ORDER BY offer DESC
            LIMIT 3;
        ''',
        [auction_uuid])
        record = cursor.fetchall()
        conn.commit()
        cursor.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500


    if len(record) == 0 or (record[0]['offer'] == 0 and record[1]['offer'] == 0 and record[2]['offer'] == 0):
        return jsonify({'response': 'There are no bids for this auction'}), 400
    
    if record[0]['closed'] == True:
        return {'response': 'Auction is already closed'}, 400
    
    try: 
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('DELETE FROM bid WHERE auction_uuid = %s',
            [auction_uuid])
        cursor.execute('UPDATE auction SET closed = TRUE WHERE uuid = %s',
            [auction_uuid])
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return {'response': str(e)}, 500

    for i in range(min(3, len(record))):
        buyer_uuid = record[i]['buyer']
        owner_uuid = record[i]['owner']
        offer = record[i]['offer']

        try:
            r = circuitbreaker.call(requests.get, f'https://player_service:5000/uuid/{buyer_uuid}', verify=False)
        except Exception as e:
            return jsonify({'response': str(e)}), 500
        if r.status_code != 200:
            continue
        buyer_data = json.loads(r.text)['response']

        if buyer_data['wallet'] < offer:
            continue

        transaction_data = {
            'uuid_player': buyer_uuid,
            'uuid_auction': auction_uuid,
            'price': offer
        }

        try:
            r = circuitbreaker.call(requests.post, 'https://transaction_service:5000/', verify=False, json=transaction_data)
        except Exception as e:
            return jsonify({'response': str(e)}), 500
        if r.status_code != 201:
            return jsonify({'response': 'Failed to create transaction', 'details': r.json()}), r.status_code
        
        amount_buyer = {
            'amount': -offer
        }

        amount_owner = {
            'amount': offer
        }
        
        try:
            r = circuitbreaker.call(requests.put, f'https://player_service:5000/{buyer_uuid}/wallet', verify=False, json=amount_buyer)
        except Exception as e:
            return jsonify({'response': str(e)}), 500
        if r.status_code != 200:
            return jsonify({'response': 'Failed to update buyer wallet', 'details': r.json()}), 500

        try:
            r = circuitbreaker.call(requests.put, f'https://player_service:5000/{owner_uuid}/wallet', verify=False, json=amount_owner)
        except Exception as e:
            return jsonify({'response': str(e)}), 500
        if r.status_code != 200:
            return jsonify({'response': 'Failed to update owner wallet', 'details': r.json()}), 500

        try:
            r = circuitbreaker.call(requests.put, f'https://gacha_service:5000/collection/user/{buyer_uuid}', verify=False, json={'gacha_uuid': record[i]['gacha_uuid'], 'q' : 1})
        except Exception as e:
            return jsonify({'response': str(e)}), 500
        if r.status_code != 200:
            return jsonify({'response': 'Failed to update buyer collection', 'details': r.json()['response']}), 500

        try:
            r = circuitbreaker.call(requests.put, f'https://gacha_service:5000/collection/user/{owner_uuid}', verify=False, json={'gacha_uuid': record[i]['gacha_uuid'], 'q' : -1})
        except Exception as e:
            return jsonify({'response': str(e)}), 500
        if r.status_code != 200:
            return jsonify({'response': 'Failed to update owner collection', 'details': r.json()['response']}), 500

        return jsonify({'response': 'Transaction completed', 'transaction': transaction_data}), 200
        
    return jsonify({'response': 'No buyers with sufficient funds'}), 200

@app.route('/market/user/<string:player_uuid>', methods=['GET'])
def show_user_auctions(player_uuid):
    records = {}

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
        cursor.execute('''SELECT id, uuid, base_price, gacha_uuid, user_uuid, to_char(expired_at, 'DD/MM/YYYY HH:MI:SSOF:00') as expired_at, closed from auction
                          WHERE user_uuid = %s''', 
                        [player_uuid])
        result = cursor.fetchall()
        if result:
            records = result
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return jsonify({'response': str(e)}), 500   

    return jsonify({'response': records}), 200 


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=(CERT_PATH, KEY_PATH))
