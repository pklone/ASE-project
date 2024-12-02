from flask import Flask, request, jsonify, abort, json, render_template
from functools import wraps
import psycopg2
import os
import requests
import jwt
import pybreaker

app = Flask(__name__)

# testing
#   curl -X GET -H 'Accept: application/json' -b cookie.jar -k https://127.0.0.1:8083/user/collection

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
  
      additional = {'auth_uuid': decoded_jwt['sub']}
  
      return f(*args, **kwargs, **additional)
  
  return decorated_function

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
        r = circuitbreaker.call(requests.post, 'https://player_service:5000', verify=False, json=player)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return r.text, r.status_code

@app.route('/user', methods=['DELETE'])
@login_required
def remove_my_user(auth_uuid):
    try:
        r = circuitbreaker.call(requests.delete, f'https://player_service:5000/uuid/{auth_uuid}', verify=False)
    except Exception as e:  
        return jsonify({'response': str(e)}), 500

    return r.text, r.status_code

@app.route('/user', methods=['PUT'])
@login_required
def update_my_user(auth_uuid):
    new_username = request.json.get('username')
    new_wallet = request.json.get('wallet')

    new_player = {
        'username': new_username,
        'wallet': new_wallet
    }

    try:
        r = circuitbreaker.call(requests.put, f'https://player_service:5000/uuid/{auth_uuid}', verify=False, json=new_player)
    except Exception as e:  
        return jsonify({'response': str(e)}), 500

    return r.text, r.status_code

@app.route('/user/collection', methods=['GET'])
@login_required
def collection(auth_uuid):
    try:
        r = circuitbreaker.call(requests.get, f'https://gacha_service:5000/collection/user/{auth_uuid}', verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500

    if 'application/json' in request.headers.get('Accept'):
        return r.text, r.status_code
    elif 'text/html' in request.headers.get('Accept'):
        try:
            records = r.json()['response']
        except ValueError:
            return jsonify({'response': 'Invalid response from gacha service'}), 500
        return render_template("user_collection.html", records=records), 200
    else:
        return jsonify({'response': 'Not supported'}), 400

@app.route('/user/currency', methods=['GET'])
@login_required
def currency(auth_uuid):
    try:
        r = circuitbreaker.call(requests.get, f'https://player_service:5000/uuid/{auth_uuid}', verify=False)
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
@login_required
def transactions_all(auth_uuid):
    try:
        r = circuitbreaker.call(requests.get, f'https://transaction_service:5000/user/{auth_uuid}', verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500
    transactions = json.loads(r.text)['response']

    if 'application/json' in request.headers['Accept']:
        return jsonify({'response': transactions}), 200
    elif 'text/html' in request.headers['Accept']:
        return render_template('transactions.html', records=transactions), 200
    else:
        return jsonify({'response': 'Not supported'}), 400

@app.route('/user/transactions/<string:transaction_uuid>', methods=['GET'])
@login_required
def transaction(transaction_uuid, auth_uuid):
    try:
        r = circuitbreaker.call(requests.get, f'https://transaction_service:5000/user/{auth_uuid}/{transaction_uuid}', verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500
    
    return r.text, r.status_code
    transaction = json.loads(r.text)['response']

    return jsonify({"response": transaction}), 200

@app.route('/userinfo', methods=['GET'])
@login_required
def userinfo(auth_uuid):
    try:
        r = circuitbreaker.call(requests.get, f'https://player_service:5000/uuid/{auth_uuid}', verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500

    return r.text, r.status_code

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=(CERT_PATH, KEY_PATH))

