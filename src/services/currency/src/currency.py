from flask import Flask, request, jsonify, abort, render_template
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

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({'response': "page not found"}), 404

@app.route('/currency/buy', methods=['GET'])
def index():
    return render_template('buy.html'), 200

@app.route('/currency/buy', methods=['POST'])
def buy():
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
    purchase = request.json.get('purchase')

    player_purchasing = {
        'player_uuid' : player_uuid,
        'purchase' : purchase
    }

    try:
        r = circuitbreaker.call(requests.post, 'https://player_service:5000/currency/buy', json=player_purchasing, verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500
    
    return r.text, r.status_code


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=(CERT_PATH, KEY_PATH))




    
