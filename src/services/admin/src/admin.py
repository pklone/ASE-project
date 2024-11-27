from flask import Flask, request, jsonify, json, make_response, render_template
from datetime import datetime
import os
import requests
import jwt
import pybreaker

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

@app.route('/admin/login', methods=['GET'])
def admin():
    return render_template('admin.html'), 200

@app.route('/admin/login', methods=['POST'])
def admin_login():
    encoded_jwt = request.cookies.get('session')

    if encoded_jwt:
        return jsonify({'response': 'Already logged in'})
    
    if request.headers.get('Content-Type') != 'application/json':
        return jsonify({'response': 'Content-type not supported'}), 400
    
    admin_username = request.json.get('username')
    admin_password = request.json.get('password')

    if not admin_username or not admin_password:
        return jsonify({'response': 'Missing credentials'}), 400
    
    data = {
        'username': admin_username,
        'password': admin_password
    }

    try:
        r = circuitbreaker.call(requests.post, 'https://authentication_service:5000/admin_login', verify=False, json=data)
    except Exception as e:
        return jsonify({'response': str(e)}), 500

    if r.status_code != 200:
        return r.text, r.status_code
    
    response = make_response(r.text)
    response.headers['Set-Cookie'] = r.headers['Set-Cookie']

    return response, r.status_code

@app.route('/admin/users', methods=['GET'])
def users():
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401
    
    try:
        r = circuitbreaker.call(requests.get, 'https://player_service:5000/', verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500
    
    return r.text, r.status_code

@app.route('/admin/users/<string:user_uuid>', methods=['GET'])
def user(user_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401
    
    try:
        r = circuitbreaker.call(requests.get, f'https://player_service:5000/uuid/{user_uuid}', verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500
    
    return r.text, r.status_code

@app.route('/admin/users/<string:user_uuid>', methods=['PUT'])
def user_modify(user_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401
    
    new_username = request.json.get('username')
    new_wallet = request.json.get('wallet')

    new_player = {
        'username': new_username,
        'wallet': new_wallet
    }

    try:
        r = circuitbreaker.call(requests.put, f'https://player_service:5000/uuid/{user_uuid}', verify=False, json=new_player)
    except Exception as e:
        return jsonify({'response': str(e)}), 500

    return r.text, r.status_code

@app.route('/admin/users/<string:user_uuid>', methods=['DELETE'])
def user_delete(user_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401

    try:
        r = circuitbreaker.call(requests.delete, f'https://player_service:5000/uuid/{user_uuid}', verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500

    return r.text, r.status_code

@app.route('/admin/collection/<string:user_uuid>', methods=['GET'])
def collection(user_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401
    
    try:
        r = circuitbreaker.call(requests.get, f'https://gacha_service:5000/collection/user/{user_uuid}', verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500

    if r.status_code != 200:
        return jsonify({'response': 'Try later - transaction service error'}), 500
    return r.text, r.status_code

@app.route('/admin/collection', methods=['POST'])
def add_gacha():
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if 'gacha_image' not in request.files:
        return {'response': 'gacha image not found'}, 400

    file = request.files['gacha_image']
    if file.filename == '':
        return {'response': 'filename not found'}, 400

    if not file:
        return {'response': 'invalid image'}, 400
    
    try:
        new_name = request.form['name']
        new_description = request.form['description']
        new_rarity = request.form['new_rarity']
    except KeyError:
        return {'response': 'Missing data'}, 400

    data = {
        'name': new_name,
        'description': new_description,
        'new_rarity': new_rarity
    }

    files = {
        'gacha_image': (file.filename, file.stream, file.mimetype)
    }

    try:
        r = circuitbreaker.call(requests.post, 'https://gacha_service:5000/collection', verify=False, data=data, files=files)
    except Exception as e:
        return jsonify({'response': str(e)}), 500

    return r.text, r.status_code

@app.route('/admin/collection/<string:gacha_uuid>', methods=['PUT'])
def modify_gacha(gacha_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401
    
    file = {}
    if 'gacha_image' in request.files:
        file = request.files['gacha_image']

        if file.filename == '':
            return {'response': 'filename not found'}, 400

        files = {
            'gacha_image': (file.filename, file.stream, file.mimetype)
        }

    data = {
        'name': request.form.get('name'),
        'description': request.form.get('description'),
        'new_rarity': request.form.get('new_rarity')
    }

    try:
        r = circuitbreaker.call(requests.put, f'https://gacha_service:5000/collection/{gacha_uuid}', verify=False, data=data, files=files)
    except Exception as e:
        return jsonify({'response': str(e)}), 500

    return r.text, r.status_code

@app.route('/admin/collection/<string:gacha_uuid>', methods=['DELETE'])
def remove_gacha(gacha_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401
    
    try:
        r = circuitbreaker.call(requests.delete, f'https://gacha_service:5000/collection/{gacha_uuid}', verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500
    
    return r.text, r.status_code

@app.route('/admin/market', methods=['GET'])
def show_all():
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401
    
    try:
        r = circuitbreaker.call(requests.get, 'https://market_service:5000/market', headers={'Accept': 'application/json'}, verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500
    
    return r.text, r.status_code

@app.route('/admin/market/<string:auction_uuid>', methods=['GET'])
def show_one(auction_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401
    
    try:
        r = circuitbreaker.call(requests.get, f'https://market_service:5000/market/{auction_uuid}', verify=False, headers={'Accept': 'application/json'})
    except Exception as e:
        return jsonify({'response': str(e)}), 500
    
    return r.text, r.status_code

@app.route('/admin/close/<string:auction_uuid>', methods=['PUT'])
def close(auction_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401
    
    try:
        r = circuitbreaker.call(requests.put, f'https://market_service:5000/market/{auction_uuid}/close', verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500
    
    return r.text, r.status_code

@app.route('/admin/transaction/<string:user_uuid>', methods=['GET'])
def transactions(user_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401
    
    try:
        r = circuitbreaker.call(requests.get, f'https://transaction_service:5000/user/{user_uuid}', verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500

    if r.status_code != 200:
        return jsonify({'response': 'Try later - transaction service error'}), 500
    
    return r.text, r.status_code
    
@app.route('/admin/payment/<string:auction_uuid>', methods=['POST'])
def payment(auction_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401
    
    try:
        r = circuitbreaker.call(requests.post, f'https://market_service:5000/market/{auction_uuid}/payment', verify=False)
    except Exception as e:
        return jsonify({'response': str(e)}), 500

    if r.status_code != 200:
        return jsonify({'response': r.text}), r.status_code
    
    return r.text, r.status_code

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=(CERT_PATH, KEY_PATH))

