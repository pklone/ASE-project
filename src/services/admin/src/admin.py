from flask import Flask, request, jsonify, json, make_response, render_template
from datetime import datetime
from functools import wraps
import os
import jwt
import re
import werkzeug.exceptions
from connectors.connector_http import AdminConnectorHTTP
from connectors.connector_http_mock import AdminConnectorHTTPMock

# testing
#   curl -X POST -s -o /dev/null -w 'Authorization: %header{Authorization}' -H 'Content-Type: application/json' -d '{"username": "admin", "password": "admin"}' -k https://127.0.0.1:8085/admin/login > headers.txt
#   curl -X GET -H @headers.txt -k https://127.0.0.1:8085/admin/users
#   curl -X GET -H @headers.txt -k https://127.0.0.1:8085/admin/users/71520f05-80c5-4cb1-b05a-a9642f9ae333
#   curl -X PUT -H @headers.txt -H 'Content-Type: application/json' -d '{"username": "placeholder", "wallet": 10}' -k https://127.0.0.1:8085/admin/users/71520f05-80c5-4cb1-b05a-a9642f9ae333
#   curl -X GET -H @headers.txt -k https://127.0.0.1:8085/admin/collection/71520f05-80c5-4cb1-b05a-a9642f9ae333
#   curl -X POST -H @headers.txt -F 'gacha_image=@batkek.jpg' -F 'name=placeholder' -F 'description=placeholder' -F 'rarity=S' -k https://127.0.0.1:8085/admin/collection
#   curl -X PUT -H @headers.txt -F 'gacha_image=@9b5.png' -F 'name=placeholder2' -F 'description=placeholder2' -F 'rarity=C' -k https://127.0.0.1:8085/admin/collection/90114331-e1ec-40d9-ac5b-8fad6bf950f8
#   curl -X GET -H @headers.txt -k https://127.0.0.1:8085/admin/market
#   curl -X GET -H @headers.txt -k https://127.0.0.1:8085/admin/market/71520f05-80c5-4cb1-b05a-a9642f9bbbbb
#   curl -X PUT -H @headers.txt -k https://127.0.0.1:8085/admin/close/71520f05-80c5-4cb1-b05a-a9642f9bbbbb
#   curl -X GET -H @headers.txt -k https://127.0.0.1:8085/admin/transaction/71520f05-80c5-4cb1-b05a-a9642f9ae33
#

class AdminService:
    UUID_REGEX = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

    def __init__(self, connectorHTTP, jwt_secret):
        self.app = Flask(__name__)

        self.__init_routes()
        self.connectorHTTP = connectorHTTP
        self.jwt_secret = jwt_secret

    # routes
    def __init_routes(self):
        self.app.add_url_rule('/admin/login',                          endpoint='admin',        view_func=self.admin,        methods=['GET'])
        self.app.add_url_rule('/admin/login',                          endpoint='admin_login',  view_func=self.admin_login,  methods=['POST'])
        self.app.add_url_rule('/admin/users',                          endpoint='users',        view_func=self.users,        methods=['GET'])
        self.app.add_url_rule('/admin/users/<string:user_uuid>',       endpoint='user',         view_func=self.user,         methods=['GET'])
        self.app.add_url_rule('/admin/users/<string:user_uuid>',       endpoint='user_modify',  view_func=self.user_modify,  methods=['PUT'])
        self.app.add_url_rule('/admin/users/<string:user_uuid>',       endpoint='user_delete',  view_func=self.user_delete,  methods=['DELETE'])
        self.app.add_url_rule('/admin/collection/<string:user_uuid>',  endpoint='collection',   view_func=self.collection,   methods=['GET'])
        self.app.add_url_rule('/admin/collection',                     endpoint='add_gacha',    view_func=self.add_gacha,    methods=['POST'])
        self.app.add_url_rule('/admin/collection/<string:gacha_uuid>', endpoint='modify_gacha', view_func=self.modify_gacha, methods=['PUT'])
        self.app.add_url_rule('/admin/collection/<string:gacha_uuid>', endpoint='remove_gacha', view_func=self.remove_gacha, methods=['DELETE'])
        self.app.add_url_rule('/admin/market',                         endpoint='show_all',     view_func=self.show_all,     methods=['GET'])
        self.app.add_url_rule('/admin/market/<string:auction_uuid>',   endpoint='show_one',     view_func=self.show_one,     methods=['GET'])
        self.app.add_url_rule('/admin/close/<string:auction_uuid>',    endpoint='close',        view_func=self.close,        methods=['PUT'])
        self.app.add_url_rule('/admin/transaction/<string:user_uuid>', endpoint='transactions', view_func=self.transactions, methods=['GET'])
        self.app.add_url_rule('/admin/payment/<string:auction_uuid>',  endpoint='payment',      view_func=self.payment,      methods=['POST'])
        self.app.register_error_handler(werkzeug.exceptions.NotFound, AdminService.page_not_found)

    # util functions
    def page_not_found(error):
        return {'response': "page not found"}, 404

    def check_uuid(**kwargs):
        res = {'name': None}
        p = re.compile(AdminService.UUID_REGEX, re.IGNORECASE)

        for key, value in kwargs.items():
            if p.match(value) is None:
                res['name'] = key
                break

        return res

    # decorators
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            encoded_jwt = request.headers.get('Authorization')
        
            if not encoded_jwt:
                return {'response': 'You\'re not logged'}, 401
            
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
            
            if decoded_jwt['scope'] != 'admin':
                return {'response': 'You are not autorized'}, 401
        
            additional = {'auth_uuid': decoded_jwt['sub']}
        
            return f(*args, **kwargs, **additional)
        
        return decorated_function

    # APIs
    def admin(self):
        return render_template('admin.html'), 200

    def admin_login(self):
        encoded_jwt = request.headers.get('Authorization')

        if encoded_jwt:
            return {'response': 'Already logged in'}, 401
        
        if request.headers.get('Content-Type') != 'application/json':
            return {'response': 'Content-type not supported'}, 400
        
        try:
            username = request.json['username']
            password = request.json['password']

            r = self.connectorHTTP.adminLogin(username, password)
        except KeyError:
            return {'response': 'Missing data'}, 400
        except Exception as e:
            return {'response': str(e)}, 500
        
        response = make_response(r['http_body'], r['http_code'])
        response.headers['Authorization'] = r['http_headers'].get('Authorization')

        return response

    @login_required
    def users(self, auth_uuid):
        try:
            r = self.connectorHTTP.getAllPlayers()
        except Exception as e:
            return {'response': str(e)}, 500
        
        return r['http_body'], r['http_code']

    @login_required
    def user(self, user_uuid, auth_uuid):
        if (res := AdminService.check_uuid(user_uuid=user_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        try:
            r = self.connectorHTTP.getPlayer(user_uuid)
        except Exception as e:
            return {'response': str(e)}, 500
        
        return r['http_body'], r['http_code']

    @login_required
    def user_modify(self, user_uuid, auth_uuid):
        if (res := AdminService.check_uuid(user_uuid=user_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        new_username = request.json.get('username')
        new_wallet = request.json.get('wallet')

        try:
            r = self.connectorHTTP.modifyPlayer(user_uuid, new_username, new_wallet)
        except Exception as e:
            return {'response': str(e)}, 500

        return r['http_body'], r['http_code']

    @login_required
    def user_delete(self, user_uuid, auth_uuid):
        if (res := AdminService.check_uuid(user_uuid=user_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        try:
            r = self.connectorHTTP.removePlayer(user_uuid)
        except Exception as e:
            return {'response': str(e)}, 500
        
        return r['http_body'], r['http_code']

    @login_required
    def collection(self, user_uuid, auth_uuid):
        if (res := AdminService.check_uuid(user_uuid=user_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        try:
            r = self.connectorHTTP.getPlayerCollection(user_uuid)
        except Exception as e:
            return {'response': str(e)}, 500
        
        return r['http_body'], r['http_code']

    @login_required
    def add_gacha(self, auth_uuid):
        if 'gacha_image' not in request.files:
            return {'response': 'gacha image not found'}, 400

        file = request.files['gacha_image']
        if file.filename == '':
            return {'response': 'filename not found'}, 400

        if not file:
            return {'response': 'invalid image'}, 400
        
        try:
            name = request.form['name']
            description = request.form['description']
            rarity = request.form['rarity']

            r = self.connectorHTTP.addGacha(name, description, rarity, file)
        except KeyError:
            return {'response': 'Missing data'}, 400
        except Exception as e:
            return {'response': str(e)}

        return r['http_body'], r['http_code']

    @login_required
    def modify_gacha(self, gacha_uuid, auth_uuid):
        if (res := AdminService.check_uuid(gacha_uuid=gacha_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        new_file = None
        if 'gacha_image' in request.files:
            new_file = request.files['gacha_image']

            if new_file.filename == '':
                return {'response': 'filename not found'}, 400

        new_name = request.form.get('name'),
        new_description = request.form.get('description'),
        new_rarity = request.form.get('rarity')
        
        try:
            r = self.connectorHTTP.modifyGacha(gacha_uuid, new_name, new_description, new_rarity, new_file)
        except Exception as e:
            return {'response': str(e)}, 500

        return r['http_body'], r['http_code']

    @login_required
    def remove_gacha(self, gacha_uuid, auth_uuid):
        if (res := AdminService.check_uuid(gacha_uuid=gacha_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        try:
            r = self.connectorHTTP.removeGacha(gacha_uuid)
        except Exception as e:
            return {'response': str(e)}, 500
        
        return r['http_body'], r['http_code']

    @login_required
    def show_all(self, auth_uuid):
        auth_header = request.headers.get('Authorization')

        try:
            r = self.connectorHTTP.getAllAuctions(auth_header)
        except Exception as e:
            return {'response': str(e)}, 500
        
        return r['http_body'], r['http_code']

    @login_required
    def show_one(self, auction_uuid, auth_uuid):
        if (res := AdminService.check_uuid(auction_uuid=auction_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        auth_header = request.headers.get('Authorization')

        try:
            r = self.connectorHTTP.getAuction(auth_header, auction_uuid)
        except Exception as e:
            return {'response': str(e)}, 500
        
        return r['http_body'], r['http_code']

    @login_required
    def close(self, auction_uuid, auth_uuid):
        if (res := AdminService.check_uuid(auction_uuid=auction_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400
        
        auth_header = request.headers.get('Authorization')

        try:
            r = self.connectorHTTP.closeAuction(auth_header, auction_uuid)
        except Exception as e:
            return {'response': str(e)}, 500
        
        return r['http_body'], r['http_code']

    @login_required
    def transactions(self, user_uuid, auth_uuid):
        if (res := AdminService.check_uuid(user_uuid=user_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        auth_header = request.headers.get('Authorization')

        try:
            r = self.connectorHTTP.getAllPlayerTransactions(auth_header, user_uuid)
        except Exception as e:
            return {'response': str(e)}, 500
        
        return r['http_body'], r['http_code']
    
    @login_required
    def payment(self, auction_uuid, auth_uuid):
        if (res := AdminService.check_uuid(auction_uuid=auction_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        try:
            r = self.connectorHTTP.paymentAuction(auction_uuid)
        except Exception as e:
            return {'response': str(e)}, 500
        
        return r['http_body'], r['http_code']

    # static factory methods
    def development(cert_path, key_path, jwt_secret):
        http = AdminConnectorHTTP()

        AdminService(http, jwt_secret).app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            ssl_context=(cert_path, key_path)
        )

    def testing(cert_path, key_path, jwt_secret):
        http = AdminConnectorHTTPMock()
        
        AdminService(http, jwt_secret).app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            ssl_context=(cert_path, key_path)
        )

    def production(cert_path, key_path, jwt_secret):
        http = AdminConnectorHTTP()
        
        AdminService(http, jwt_secret).app.run(
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
            AdminService.production(CERT_PATH, KEY_PATH, JWT_SECRET)
        case 'testing':
            AdminService.testing(CERT_PATH, KEY_PATH, JWT_SECRET)
        case 'development':
            AdminService.development(CERT_PATH, KEY_PATH, JWT_SECRET)

