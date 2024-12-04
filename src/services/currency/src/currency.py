from flask import Flask, request, jsonify, abort, render_template
from functools import wraps
import requests
import jwt
import pybreaker
import os

app = Flask(__name__)

circuitbreaker = pybreaker.CircuitBreaker(
    fail_max=5, 
    reset_timeout=60*5
)

CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH = os.getenv("KEY_PATH")

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

@app.route('/currency/buy', methods=['GET'])
def index():
    return render_template('buy.html'), 200

@app.route('/currency/buy', methods=['PUT'])
@login_required
def buy(auth_uuid):
    amount = request.json.get('purchase')

    if amount <= 0:
        return jsonify({'response': 'Invalid purchase'}), 400
    
    amount = {'amount': amount}

    try:
        r = circuitbreaker.call(requests.put, f'https://player_service:5000/{auth_uuid}/wallet', json=amount, verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500
    
    return r.text, r.status_code


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=(CERT_PATH, KEY_PATH))




    
