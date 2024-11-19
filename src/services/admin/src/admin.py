from flask import Flask, request, jsonify, json, make_response, render_template
from datetime import datetime
import os
import requests
import jwt

app = Flask(__name__)

SECRET = 'secret' # change secret for deployment

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

    #try:
    #    r_json = json.loads(r.text)
    #except json.JSONDecodeError as e:
    #    return jsonify({'response': 'Json error'}), 500

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
    
    r = requests.get(url='http://account_service:5000/users')

    try:
        response = json.loads(r.text)
    except json.JSONDecodeError as e:
        return jsonify({'response': 'Json error'}), 500
    
    return response

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
    
    
    r = requests.get(url=f'http://account_service:5000/users/{user_uuid}')

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

    r = requests.put(url=f'http://account_service:5000/users/{user_uuid}', json=new_player)

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
    
    new_name = request.json.get('name')
    new_description = request.json.get('description')
    new_image_path = request.json.get('image_path')
    new_rarity = request.json.get('id_rarity')

    new_gacha = {
        'name': new_name,
        'description': new_description,
        'image_path': new_image_path,
        'new_rarity': new_rarity
    }

    r = requests.post(url=f'http://gacha_service:5000/collection', json=new_gacha)

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

#TODO aggiungere admin functionality market(to add) player(to add) currency(to add)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

