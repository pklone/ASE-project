from flask import Flask, request, jsonify, abort, json, render_template
from functools import wraps
import os
import jwt
import re
import werkzeug.exceptions
from connectors.connector_http import AccountConnectorHTTP
from connectors.connector_http_mock import AccountConnectorHTTPMock

# testing
#   curl -X POST -H 'Content-Type: application/json' -d '{"username": "kek", "password": "kek"}' -k https://127.0.0.1:8083/user
#   curl -X POST -s -o /dev/null -w 'Authorization: %header{Authorization}' -H 'Content-Type: application/json' -d '{"username": "test", "password": "test"}' -k https://127.0.0.1:8081 > headers.txt
#       curl -X GET -H 'Accept: application/json' -H @headers.txt -k https://127.0.0.1:8083/user/collection
#       curl -X DELETE -H @headers.txt -k https://127.0.0.1:8083/user
#       curl -X PUT -H 'Content-Type: application/json' -H @headers.txt -d '{"username": "kek", "wallet": 100}' -k https://127.0.0.1:8083/user
#       curl -X GET -H 'Accept: application/json' -H @headers.txt -k https://127.0.0.1:8083/user/currency
#       curl -X GET -H 'Accept: application/json' -H @headers.txt -k https://127.0.0.1:8083/user/transactions
#       curl -X GET -H 'Accept: application/json' -H @headers.txt -k https://127.0.0.1:8083/user/transactions/3b8009f2-31c8-484b-aa74-32defbb02985

class AccountService:
    UUID_REGEX = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

    def __init__(self, connectorHTTP, jwt_secret):
        self.app = Flask(__name__)

        self.__init_routes()
        self.connectorHTTP = connectorHTTP
        self.jwt_secret = jwt_secret

    # routes
    def __init_routes(self):
        self.app.add_url_rule('/user',                                        endpoint='signup',           view_func=self.signup,           methods=['GET'])
        self.app.add_url_rule('/user',                                        endpoint='create',           view_func=self.create,           methods=['POST'])
        self.app.add_url_rule('/user',                                        endpoint='remove_my_user',   view_func=self.remove_my_user,   methods=['DELETE'])
        self.app.add_url_rule('/user',                                        endpoint='update_my_user',   view_func=self.update_my_user,   methods=['PUT'])
        self.app.add_url_rule('/user/collection',                             endpoint='collection',       view_func=self.collection,       methods=['GET'])
        self.app.add_url_rule('/user/currency',                               endpoint='currency',         view_func=self.currency,         methods=['GET'])
        self.app.add_url_rule('/user/transactions',                           endpoint='transactions_all', view_func=self.transactions_all, methods=['GET'])
        self.app.add_url_rule('/user/transactions/<string:transaction_uuid>', endpoint='transaction',      view_func=self.transaction,      methods=['GET'])
        self.app.add_url_rule('/userinfo',                                    endpoint='userinfo',         view_func=self.userinfo,         methods=['GET'])
        self.app.register_error_handler(werkzeug.exceptions.NotFound, AccountService.page_not_found)

    # util functions
    def page_not_found(error):
        return {'response': "page not found"}, 404

    def check_uuid(**kwargs):
        res = {'name': None}
        p = re.compile(AccountService.UUID_REGEX, re.IGNORECASE)

        for key, value in kwargs.items():
            if p.match(value) is None:
                res['name'] = key
                break

        return res

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
                return jsonify({'response': 'Expired token'}), 403
            except jwt.InvalidTokenError:
                return jsonify({'response': 'Invalid token'}), 403
        
            if 'sub' not in decoded_jwt:
                return jsonify({'response': 'Try later'}), 403

            if decoded_jwt['scope'] != 'player':
                return jsonify({'response': 'You are not authorized'}), 401
        
            additional = {'auth_uuid': decoded_jwt['sub']}
        
            return f(*args, **kwargs, **additional)
        
        return decorated_function

    # APIs
    def signup(self):
        return render_template('signup.html'), 200

    def create(self):
        try:
            username = request.json['username']
            password = request.json['password']

            r = self.connectorHTTP.createPlayer(username, password)
        except KeyError:
            return {'response': 'Missing data'}, 400
        except Exception as e:
            return {'response': str(e)}, 500
        
        return r['http_body'], r['http_code']

    @login_required
    def remove_my_user(self, auth_uuid):
        auth_header = request.headers.get('Authorization')

        try:
            r = self.connectorHTTP.getAllAuctions(auth_header)
            if r['http_code'] != 200:
                return {'response': 'Try later'}, 500

            for auction in r['http_body']['response']:
                if auction["Player"]['uuid'] == auth_uuid and not auction['closed']:
                    return {'response': 'You have an active auction'}, 400

            r = self.connectorHTTP.removePlayer(auth_uuid)

            if r['http_code'] != 200:
                return {'response': 'Try later'}, 500
        except Exception as e:
            return {'response': str(e)}, 500
        
        return r['http_body'], r['http_code']

    @login_required
    def update_my_user(self, auth_uuid):
        try:
            new_username = request.json['username']
            new_wallet = request.json['wallet']

            if type(new_wallet) is not int or new_wallet < 0:
                return {'response': 'Invalid amount'}, 400

            r = self.connectorHTTP.modifyPlayer(auth_uuid, new_username, new_wallet)

            if r['http_code'] != 200:
                return {'response': 'Try later'}, 500
        except KeyError:
            return {'response': 'Missing data'}, 400
        except Exception as e:
            return {'response': str(e)}, 500
        
        return r['http_body'], 200

    @login_required
    def collection(self, auth_uuid):
        try:
            r = self.connectorHTTP.playerCollection(auth_uuid)

            if r['http_code'] != 200:
                return {'response': 'Try later'}, 500
        except Exception as e:
            return {'response': str(e)}, 500

        if 'application/json' in request.headers.get('Accept'):
            return r['http_body'], 200
        elif 'text/html' in request.headers.get('Accept'):
            return render_template("user_collection.html", records=r['http_body']['response']), 200
        else:
            return {'response': 'Not supported'}, 400

    @login_required
    def currency(self, auth_uuid):
        try:
            r = self.connectorHTTP.getPlayer(auth_uuid)
            
            if r['http_code'] != 200:
                return {'response': 'Try later'}, 500
        except Exception as e:
            return {'response': str(e)}, 500

        wallet = r['http_body']['response']['wallet']

        if 'application/json' in request.headers.get('Accept'):
            return {'response': wallet}, 200
        elif 'text/html' in request.headers.get('Accept'):
            return render_template("currency.html", wallet=wallet), 200
        else:
            return {'response': 'Not supported'}, 406

    @login_required
    def transactions_all(self, auth_uuid):
        try:
            r = self.connectorHTTP.getAllTransactions(auth_uuid)
            
            if r['http_code'] != 200:
                return {'response': 'Try later'}, 500
        except Exception as e:
            return jsonify({'response': str(e)}), 500

        if 'application/json' in request.headers['Accept']:
            return r['http_body'], 200
        elif 'text/html' in request.headers['Accept']:
            return render_template('transactions.html', records=r['http_body']['response']), 200
        else:
            return {'response': 'Not supported'}, 400

    @login_required
    def transaction(self, transaction_uuid, auth_uuid):
        if (res := AccountService.check_uuid(transaction_uuid=transaction_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        try:
            r = self.connectorHTTP.getTransaction(auth_uuid, transaction_uuid)
            
            if r['http_code'] != 200:
                return {'response': 'Try later'}, 500
        except Exception as e:
            return {'response': str(e)}, 500

        return r['http_body'], 200

    @login_required
    def userinfo(self, auth_uuid):
        try:
            r = self.connectorHTTP.getPlayer(auth_uuid)

            if r['http_code'] != 200:
                return {'response': 'Try later'}, 500
        except Exception as e:
            return {'response': str(e)}, 500
        
        return r['http_body'], r['http_code']

    # static factory methods
    def development(cert_path, key_path, jwt_secret):
        http = AccountConnectorHTTP()

        AccountService(http, jwt_secret).app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            ssl_context=(cert_path, key_path)
        )

    def testing(cert_path, key_path, jwt_secret):
        http = AccountConnectorHTTPMock()
        
        AccountService(http, jwt_secret).app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            ssl_context=(cert_path, key_path)
        )

    def production(cert_path, key_path, jwt_secret):
        http = AccountConnectorHTTP()
        
        AccountService(http, jwt_secret).app.run(
            host="0.0.0.0", 
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
            AccountService.production(CERT_PATH, KEY_PATH, JWT_SECRET)
        case 'testing':
            AccountService.testing(CERT_PATH, KEY_PATH, JWT_SECRET)
        case 'development':
            AccountService.development(CERT_PATH, KEY_PATH, JWT_SECRET)

