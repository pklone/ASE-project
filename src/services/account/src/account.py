from flask import Flask, request, jsonify, abort
import psycopg2
import os
import requests

app = Flask(__name__)

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
    return jsonify({'response': 'ok!'})

@app.route('/user', methods=['PUT'])
def update():
    return jsonify({'response': 'ok!'})

@app.route('/user/collection', methods=['GET'])
def collection():
    return jsonify({'response': 'ok!'})

@app.route('/user/currency', methods=['GET'])
def currency():
    return jsonify({'response': 'ok!'})

@app.route('/user/transactions', methods=['GET'])
def transactions_all():
    return jsonify({'response': 'ok!'})

@app.route('/user/transactions/<string:transaction_uuid>', methods=['GET'])
def transaction(transaction_uuid):
    return jsonify({'response': 'ok!'})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

