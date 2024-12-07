from flask import Flask, request, jsonify, abort, render_template, make_response
from functools import wraps
import requests
import jwt
import pybreaker
import os
import jwt
import werkzeug.exceptions
from functools import wraps
from connectors.connector_http import CurrencyConnectorHTTP
from connectors.connector_http_mock import CurrencyConnectorHTTPMock

# testing
#   curl -X POST -s -o /dev/null -w 'Authorization: %header{Authorization}' -H 'Content-Type: application/json' -d '{"username": "test", "password": "test"}' -k https://127.0.0.1:8081/login > headers.txt
#       curl -X PUT -H @headers.txt -H 'Content-Type: application/json' -d '{"purchase": 100}' -k https://127.0.0.1:8088/currency/buy 

class CurrencyService:
    def __init__(self, connectorHTTP, jwt_secret):
        self.app = Flask(__name__)

        self.__init_routes()
        self.connectorHTTP = connectorHTTP
        self.jwt_secret = jwt_secret

    # routes
    def __init_routes(self):
        self.app.add_url_rule('/currency/buy', endpoint='index', view_func=self.index, methods=['GET'])
        self.app.add_url_rule('/currency/buy', endpoint='buy',   view_func=self.buy,   methods=['PUT'])
        self.app.register_error_handler(werkzeug.exceptions.NotFound, CurrencyService.page_not_found)

    # util functions
    def page_not_found(error):
        return {'response': "page not found"}, 404

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
        
                decoded_jwt = jwt.decode(encoded_jwt, args[0].jwt_secret, algorithms=['HS256'], options=options)
            except jwt.ExpiredSignatureError:
                return {'response': 'Expired token'}, 403
            except jwt.InvalidTokenError:
                return {'response': 'Invalid token'}, 403
        
            if 'sub' not in decoded_jwt:
                return {'response': 'Try later'}, 403

            if decoded_jwt['scope'] != 'player':
                return jsonify({'response': 'You are not autorized'}), 401
        
            additional = {'auth_uuid': decoded_jwt['sub']}
        
            return f(*args, **kwargs, **additional)
        
        return decorated_function

    # APIs
    def index(self):
        return render_template('buy.html'), 200

    @login_required
    def buy(self, auth_uuid):
        try:
            amount = request.json['purchase']

            if type(amount) is not int or amount <= 0:
                return {'response': 'Invalid amount'}, 400

            r = self.connectorHTTP.playerWallet(auth_uuid, amount)
            
            if r['http_code'] != 200:
                return {'response': 'Try later'}, 500
        except KeyError:
            return {'response': 'Missing data'}, 400
        except Exception as e:
            return {'response': str(e)}, 500
        
        response = make_response(r['http_body'], r['http_code'])
        response.headers['Content-Type'] = 'application/json'
        
        return response

    # static factory methods
    def development(cert_path, key_path, jwt_secret):
        http = CurrencyConnectorHTTP()

        CurrencyService(http, jwt_secret).app.run(
            host="0.0.0.0", # nosec B104 - Safe in Docker 
            port=5000, 
            debug=True, # nosec B201 Those methods are only for development or testing 
            ssl_context=(cert_path, key_path)
        )

    def testing(cert_path, key_path, jwt_secret):
        http = CurrencyConnectorHTTPMock()
        
        CurrencyService(http, jwt_secret).app.run(
            host="0.0.0.0", # nosec B104 - Safe in Docker 
            port=5000, 
            debug=True, # nosec B201 Those methods are only for development or testing 
            ssl_context=(cert_path, key_path)
        )

    def production(cert_path, key_path, jwt_secret):
        http = CurrencyConnectorHTTP()
        
        CurrencyService(http, jwt_secret).app.run(
            host="0.0.0.0", # nosec B104 - Safe in Docker 
            port=5000, 
            ssl_context=(cert_path, key_path)
        )

if __name__ == '__main__':
    # set https certs
    CERT_PATH = os.getenv("CERT_PATH")
    KEY_PATH = os.getenv("KEY_PATH")

    # set jwt
    JWT_SECRET = os.getenv("JWT_SECRET")

    # deployment mode
    DEPLOYMENT_MODE = os.getenv("DEPLOYMENT_MODE")

    match DEPLOYMENT_MODE:
        case 'production':
            CurrencyService.production(CERT_PATH, KEY_PATH, JWT_SECRET)
        case 'testing':
            CurrencyService.testing(CERT_PATH, KEY_PATH, JWT_SECRET)
        case 'development':
            CurrencyService.development(CERT_PATH, KEY_PATH, JWT_SECRET)




    
