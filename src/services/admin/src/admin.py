from flask import Flask, request, jsonify, json, make_response, render_template
from datetime import datetime
import os
import requests
import jwt

app = Flask(__name__)

SECRET = 'secret' # change secret for deployment

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({'response': "page not found"}), 404

@app.route('/admin/login', methods=['GET'])
def admin():
    return render_template('admin.html')

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

    r = requests.post(url='http://authentication_service:5000/admin_login', json=data)

    if r.status_code != 200:
        return r.text, r.status_code
    
    response = make_response(r.text)
    response.headers['Set-Cookie'] = r.headers['Set-Cookie']

    return response

@app.route('/admin/users', methods=['GET'])
def users():
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'})
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'})
    
    r = requests.get(url='http://player_service:5000/')

    try:
        response = json.loads(r.text)
    except json.JSONDecodeError as e:
        return jsonify({'response': 'Json error'}), 500
    
    return jsonify(response['response']), 200

@app.route('/admin/users/<string:user_uuid>', methods=['GET'])
def user(user_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'})
    
    if decoded_jwt['admin'] == False:
        return response
    
    
    r = requests.get(url=f'http://player_service:5000/uuid/{user_uuid}')

    try:
        response = json.loads(r.text)
    except json.JSONDecodeError as e:
        return jsonify({'response': 'Json error'}), 500
    
    return jsonify(response), 200

@app.route('/admin/users/<string:user_uuid>', methods=['PUT'])
def user_modify(user_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'})
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'})
    
    new_username = request.json.get('username')
    new_wallet = request.json.get('wallet')

    new_player = {
        'username': new_username,
        'wallet': new_wallet
    }

    r = requests.put(url=f'http://player_service:5000/uuid/{user_uuid}', json=new_player)

    return r.text

@app.route('/admin/collection', methods=['POST'])
def add_gacha():
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if 'gacha_image' not in request.files:
        return {'response': 'gacha image not found'}

    file = request.files['gacha_image']
    if file.filename == '':
        return {'response': 'filename not found'}

    if not file:
        return {'response': 'invalid image'}
    
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

    r = requests.post(url=f'http://gacha_service:5000/collection', data=data, files=files)

    return r.text

@app.route('/admin/collection/<string:gacha_uuid>', methods=['PUT'])
def modify_gacha(gacha_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401
    
    new_name = request.json.get('name')
    new_description = request.json.get('description')
    new_image_path = request.json.get('image_path')
    new_rarity = request.json.get('id_rarity')
    if new_rarity <= 0 or new_rarity > 5:
        return jsonify({'response': 'Invalid rarity'})
    
    mod_gacha = {
        'new_name': new_name,
        'new_description': new_description,
        'new_image_path': new_image_path,
        'new_rarity': new_rarity
    }
    
    r = requests.put(url=f'http://gacha_service:5000/collection/{gacha_uuid}', json=mod_gacha)
    
    return r.text

@app.route('/admin/market', methods=['GET'])
def show_all():
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'})
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'})
    
    r = requests.get(url='http://market_service:5000/market')

    try:
        response = json.loads(r.text)
    except json.JSONDecodeError as e:
        return jsonify({'response': 'Json error'}), 500
    
    return jsonify(response['response']), 200

@app.route('/admin/market/<string:auction_uuid>', methods=['GET'])
def show_one(auction_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'})
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'})
    
    r = requests.get(url=f'http://market_service:5000/market/{auction_uuid}', headers={'Accept': 'application/json'})

    try:
        response = json.loads(r.text)
    except json.JSONDecodeError as e:
        return jsonify({'response': 'Json error'}), 500
    
    return jsonify(response['response']), 200

@app.route('/admin/close/<string:auction_uuid>', methods=['PUT'])
def close(auction_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'}), 401
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'}), 401
    
    r = requests.put(f'http://market_service:5000/market/{auction_uuid}/close')
    return r.text, r.status_code

@app.route('/admin/transaction/<string:player_uuid>', methods=['GET'])
def transactions(player_uuid):
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

    if 'admin' not in decoded_jwt:
        return jsonify({'response': 'You are not autorized'})
    
    if decoded_jwt['admin'] == False:
        return jsonify({'response': 'You are not autorized'})
    
    r = requests.get(url=f"http://transaction_service:5000/user/{player_uuid}")
    if r.status_code != 200:
        return jsonify({'response': 'Try later - transaction service error'})
    return r.text, 200
    

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

