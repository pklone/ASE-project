from flask import Flask, request, jsonify, abort, json, render_template
import psycopg2
import os
import requests
import jwt
import pybreaker

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

# set jwt
SECRET = os.getenv("JWT_SECRET")

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({'response': "page not found"}), 404

@app.route('/user', methods=['GET'])
def signup():
    return render_template('signup.html'), 200

@app.route('/user', methods=['POST'])
def create():
    username = request.json['username']
    password = request.json['password']

    player = {
        'username': username,
        'password': password
    }

    try:
        r = circuitbreaker.call(requests.post, 'http://player_service:5000', json=player)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return r.text, r.status_code

@app.route('/user', methods=['DELETE'])
def remove():
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
        r = circuitbreaker.call(requests.delete, f'http://player_service:5000/uuid/{player_uuid}')
    except Exception as e:  
        return jsonify({'response': str(e)}), 500

    return r.text, r.status_code

@app.route('/user', methods=['PUT'])
def update():
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

    new_username = request.json.get('username')
    new_wallet = request.json.get('wallet')

    new_player = {
        'username': new_username,
        'wallet': new_wallet
    }

    try:
        r = circuitbreaker.call(requests.put, f'http://player_service:5000/uuid/{player_uuid}', json=new_player)
    except Exception as e:  
        return jsonify({'response': str(e)}), 500

    return r.text, r.status_code

@app.route('/user/collection', methods=['GET'])
def collection():
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
    except jwt.InvalidTokenError as e:
        return jsonify({'response': "Invalid token"}), 403

    if 'uuid' not in decoded_jwt:
        return jsonify({'response': 'Try later'}), 403

    player_uuid = decoded_jwt['uuid']

    try:
        r = circuitbreaker.call(requests.get, f'http://gacha_service:5000/collection/user/{player_uuid}')
    except Exception as e:
        return jsonify({'response': str(e)}), 500

    return r.text, r.status_code

@app.route('/user/currency', methods=['GET'])
def currency():
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
        r = circuitbreaker.call(requests.get, f'http://player_service:5000/uuid/{player_uuid}')
    except Exception as e:
        return jsonify({'response': str(e)}), 500

    wallet = json.loads(r.text)['response']['wallet']

    if 'application/json' in request.headers.get('Accept'):
        return jsonify({'response': wallet}), 200
    elif 'text/html' in request.headers.get('Accept'):
        return render_template("currency.html", wallet=wallet), 200
    else:
        return jsonify({'response': 'Not supported'}), 406

@app.route('/user/transactions', methods=['GET'])
def transactions_all():
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
        r = circuitbreaker.call(requests.get, f'http://transaction_service:5000/user/{player_uuid}')
    except Exception as e:
        return jsonify({'response': str(e)}), 500
    transactions = json.loads(r.text)['response']

    return jsonify({"response": transactions}), 200

@app.route('/user/transactions/<string:transaction_uuid>', methods=['GET'])
def transaction(transaction_uuid):
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
        r = circuitbreaker.call(requests.get, f'http://transaction_service:5000/user/{player_uuid}/{transaction_uuid}')
    except Exception as e:
        return jsonify({'response': str(e)}), 500
    
    return r.text, r.status_code
    transaction = json.loads(r.text)['response']

    return jsonify({"response": transaction}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

