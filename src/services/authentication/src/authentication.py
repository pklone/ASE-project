from flask import Flask, request, jsonify, make_response, json, render_template
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import os
import werkzeug.exceptions
from connectors.connector_db import AuthenticationConnectorDB
from connectors.connector_db_mock import AuthenticationConnectorDBMock
from connectors.connector_http import AuthenticationConnectorHTTP
from connectors.connector_http_mock import AuthenticationConnectorHTTPMock

# if r['http_code'] != 200:
#    return {'response': r['http_body']['response']}, 500

# testing
#   curl -X POST -s -o /dev/null -w 'Authorization: %header{Authorization}' -H 'Content-Type: application/json' -d '{"username": "test", "password": "test"}' -k https://127.0.0.1:8081 > headers.txt
#   curl -X DELETE -H @headers.txt -k https://127.0.0.1:8081/logout

class AuthenticationService:
    def __init__(self, connectorHTTP, connectorDB, jwt_secret):
        self.app = Flask(__name__)

        self.__init_routes()
        self.connectorHTTP = connectorHTTP
        self.connectorDB = connectorDB
        self.jwt_secret = jwt_secret

    # routes
    def __init_routes(self):
        self.app.add_url_rule('/login',       endpoint='index',       view_func=self.index,       methods=['GET'])
        self.app.add_url_rule('/admin_login', endpoint='admin_login', view_func=self.admin_login, methods=['POST'])
        self.app.add_url_rule('/login',       endpoint='login',       view_func=self.login,       methods=['POST'])
        self.app.add_url_rule('/logout',      endpoint='logout',      view_func=self.logout,      methods=['DELETE'])
        self.app.register_error_handler(werkzeug.exceptions.NotFound, AuthenticationService.page_not_found)

    # util functions
    def page_not_found(error):
        return {'response': "page not found"}, 404

    # APIs
    def index(self):
        return render_template('index.html'), 200

    def admin_login(self):
        if request.headers.get('Content-Type') != 'application/json':
            return {'response': 'Content-type not supported'}, 400

        encoded_jwt = request.headers.get('Authorization')

        if encoded_jwt:
            return {'response': 'Already logged in'}, 200

        try:
            admin_username = request.json['username']
            admin_password = request.json['password']

            record = self.connectorDB.getAdminByUsername(admin_username)
            if not bcrypt.checkpw(admin_password.encode(), record['password_hash'].encode()):
                return {'response': 'Invalid credentials'}, 401

        except KeyError:
            return {'response': 'Missing data'}, 400
        except ValueError as e:
            return {'response': str(e)}, 400
        except Exception as e:
            return {'response': str(e)}, 500

        expire = datetime.now(tz=timezone.utc) + timedelta(seconds=3600)
        time = datetime.now(tz=timezone.utc)

        payload_access = {
            'iss': 'https://ase.localhost',
            'sub': record['uuid'], 
            'exp': expire,
            'scope': 'admin'
        }

        payload_id = {
            'iss': 'https://ase.localhost',
            'aud': 'https://ase.localhost/login',
            'sub': record['uuid'], 
            'exp': expire,
            'iat': time,
            'nbf': time,
            'scope': 'admin'
        }

        access_token = jwt.encode(payload_access, self.jwt_secret, algorithm='HS256')
        id_token = jwt.encode(payload_id, self.jwt_secret, algorithm='HS256')

        response = {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'id_token': id_token
        }

        headers = {
            'Authorization': f'Bearer {access_token}',
        }

        response = make_response(jsonify(response))
        response.headers = headers

        return response, 200

    def login(self):
        if request.headers.get('Content-Type') != 'application/json':
            return {'response': 'Content-type not supported'}, 400

        encoded_jwt = request.headers.get('Authorization')

        if encoded_jwt:
            return {'response': 'Already logged in'}, 200

        try:
            username = request.json['username']
            password = request.json['password']

            r = self.connectorHTTP.getPlayerWithPasswordHashByUsername(username)
            if r['http_code'] != 200:
                return {'response': r['http_body']['response']}, 500

            player = r['http_body']['response']

            if player["active"] == False:
                return {'response': 'Account not found'}, 401

            if not bcrypt.checkpw(password.encode(), player['password_hash'].encode()):
                return {'response': 'Invalid credentials'}, 401

        except KeyError:
            return {'response': 'Missing credentials'}, 400
        except ValueError as e:
            return {'response': str(e)}, 400
        except Exception as e:
            return {'response': str(e)}, 500

        expire = datetime.now(tz=timezone.utc) + timedelta(seconds=3600)
        time = datetime.now(tz=timezone.utc)

        payload_access = {
            'iss': 'https://ase.localhost',
            'sub': player['uuid'], 
            'exp': expire,
            'scope': 'player'
        }

        payload_id = {
            'iss': 'https://ase.localhost',
            'aud': 'https://ase.localhost/login',
            'sub': player['uuid'], 
            'scope': 'player',
            'exp': expire,
            'iat': time,
            'nbf': time
        }

        access_token = jwt.encode(payload_access, self.jwt_secret, algorithm='HS256')
        id_token = jwt.encode(payload_id,  self.jwt_secret, algorithm='HS256')

        response = {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'id_token': id_token
        }

        headers = {
            'Authorization': f'Bearer {access_token}',
        }

        response = make_response(jsonify(response))
        response.headers = headers

        return response, 200

    def logout(self):
        encoded_jwt = request.headers.get('Authorization')

        if not encoded_jwt:
            return {'response': 'You are not logged'}, 401

        return {'response': 'Logout successful'}, 200

    # static factory methods
    def development(db_name, db_user, db_password, db_host, db_port, db_sslmode, cert_path, key_path, jwt_secret):
        db = AuthenticationConnectorDB(db_name, db_user, db_password, db_host, db_port, db_sslmode)
        http = AuthenticationConnectorHTTP()

        AuthenticationService(http, db, jwt_secret).app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            ssl_context=(cert_path, key_path)
        )

    def testing(cert_path, key_path, jwt_secret):
        db = AuthenticationConnectorDBMock()
        http = AuthenticationConnectorHTTPMock()
        
        AuthenticationService(http, db, jwt_secret).app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            ssl_context=(cert_path, key_path)
        )

    def production(db_name, db_user, db_password, db_host, db_port, db_sslmode, cert_path, key_path, jwt_secret):
        db = AuthenticationConnectorDB(db_name, db_user, db_password, db_host, db_port, db_sslmode)
        http = AuthenticationConnectorHTTP()
        
        AuthenticationService(http, db, jwt_secret).app.run(
            host="0.0.0.0", 
            port=5000, 
            ssl_context=(cert_path, key_path)
        )

if __name__ == '__main__':
    # set db connection
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    POSTGRES_SSLMODE = os.getenv("POSTGRES_SSLMODE")

    # set https certs
    CERT_PATH = os.getenv("CERT_PATH")
    KEY_PATH = os.getenv("KEY_PATH")

    # set jwt
    JWT_SECRET = os.getenv("JWT_SECRET")

    # deployment mode
    DEPLOYMENT_MODE = os.getenv("DEPLOYMENT_MODE")

    match DEPLOYMENT_MODE:
        case 'production':
            AuthenticationService.production(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, POSTGRES_SSLMODE, CERT_PATH, KEY_PATH, JWT_SECRET)
        case 'testing':
            AuthenticationService.testing(CERT_PATH, KEY_PATH, JWT_SECRET)
        case 'development':
            AuthenticationService.development(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, POSTGRES_SSLMODE, CERT_PATH, KEY_PATH, JWT_SECRET)