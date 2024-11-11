from flask import Flask, request, jsonify, abort, json
import psycopg2
import os
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

@app.route('/user', methods=['POST'])
def create():
    username = request.json['username']
    password = request.json['password']

    player = {
        'username': username,
        'password': password
    }

    r = requests.post(url='http://player_service:5000', json=player)
    
    return r.text

@app.route('/user', methods=['DELETE'])
def remove():
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
    r = requests.delete(f'http://player_service:5000/uuid/{player_uuid}')

    return r.text

@app.route('/user', methods=['PUT'])
def update():
    return jsonify({'response': 'ok!'})

@app.route('/user/collection', methods=['GET'])
def collection():
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
    r = requests.get(f'http://player_service:5000/uuid/{player_uuid}')
    player = json.loads(r.text)['response']

    r = requests.get(f'http://gacha_service:5000/collection/user/{player['id']}')

    return r.text

@app.route('/user/currency', methods=['GET'])
def currency():
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
    r = requests.get(f'http://player_service:5000/uuid/{player_uuid}')
    wallet = json.loads(r.text)['response']['wallet']

    return jsonify({"response": wallet})

@app.route('/user/transactions', methods=['GET'])
def transactions_all():
    return jsonify({'response': 'ok!'})

@app.route('/user/transactions/<string:transaction_uuid>', methods=['GET'])
def transaction(transaction_uuid):
    return jsonify({'response': 'ok!'})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

