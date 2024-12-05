from flask import Flask, request, jsonify, abort
import psycopg2
import psycopg2.extras
import os
import uuid
import bcrypt
import re
import werkzeug.exceptions
from functools import wraps
from connectors.connector_db import PlayerConnectorDB
from connectors.connector_db_mock import PlayerConnectorDBMock

# testing
#   curl -X GET -k https://127.0.0.1:8080
#   curl -X GET -k https://127.0.0.1:8080/id/4
#   curl -X GET -k https://127.0.0.1:8080/uuid/71520f05-80c5-4cb1-b05a-a9642f9ae222
#   curl -X PUT -H 'Content-Type: application/json' -d '{"username": "placeholder", "wallet": 10}' -k https://127.0.0.1:8080/uuid/71520f05-80c5-4cb1-b05a-a9642f9ae222
#   curl -X GET -k https://127.0.0.1:8080/username/placeholder
#   curl -X POST -H 'Content-Type: application/json' -d '{"username": "kek", "password": "kek"}' -k https://127.0.0.1:8080
#   curl -X DELETE -k https://127.0.0.1:8080/id/5
#   curl -X DELETE -k https://127.0.0.1:8080/uuid/71520f05-80c5-4cb1-b05a-a9642f9ae222
#   curl -X PUT -H 'Content-Type: application/json' -d '{"amount": 20}' -k https://127.0.0.1:8080/71520f05-80c5-4cb1-b05a-a9642f9ae333/wallet

class PlayerService:
    UUID_REGEX = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

    def __init__(self, connectorDB):
        self.app = Flask(__name__)

        self.__init_routes()
        self.connectorDB = connectorDB

    # routes
    def __init_routes(self):
        self.app.add_url_rule('/',                                           endpoint='show_all',                            view_func=self.show_all,                            methods=['GET'])
        self.app.add_url_rule('/id/<int:player_id>',                         endpoint='show_by_id',                          view_func=self.show_by_id,                          methods=['GET'])
        self.app.add_url_rule('/uuid/<string:player_uuid>',                  endpoint='show_by_uuid',                        view_func=self.show_by_uuid,                        methods=['GET'])
        self.app.add_url_rule('/uuid/<string:player_uuid>',                  endpoint='modify_by_uuid',                      view_func=self.modify_by_uuid,                      methods=['PUT'])
        self.app.add_url_rule('/username/<string:player_username>',          endpoint='show_by_username',                    view_func=self.show_by_username,                    methods=['GET'])
        self.app.add_url_rule('/username/<string:player_username>/all',      endpoint='show_with_password_hash_by_username', view_func=self.show_with_password_hash_by_username, methods=['GET'])
        self.app.add_url_rule('/',                                           endpoint='create',                              view_func=self.create,                              methods=['POST'])
        self.app.add_url_rule('/id/<int:player_id>',                         endpoint='remove_by_id',                        view_func=self.remove_by_id,                        methods=['DELETE'])
        self.app.add_url_rule('/uuid/<string:player_uuid>',                  endpoint='remove_by_uuid',                      view_func=self.remove_by_uuid,                      methods=['DELETE'])
        self.app.add_url_rule('/<string:player_uuid>/wallet',                endpoint='update_wallet',                       view_func=self.update_wallet,                       methods=['PUT'])
        self.app.register_error_handler(werkzeug.exceptions.NotFound, PlayerService.page_not_found)

    # util functions
    def page_not_found(error):
        return {'response': "page not found"}, 404

    def check_uuid(**kwargs):
        res = {'name': None}
        p = re.compile(PlayerService.UUID_REGEX, re.IGNORECASE)

        for key, value in kwargs.items():
            if p.match(value) is None:
                res['name'] = key
                break

        return res

    # APIs
    def show_all(self):
        try:
            records = self.connectorDB.getAll()
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': records}, 200

    def show_by_id(self, player_id):
        try:
            record = self.connectorDB.getById(player_id)
        except ValueError as e:
            return {'response': str(e)}, 400       
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': record}, 200

    def show_by_uuid(self, player_uuid):
        if (res := PlayerService.check_uuid(player_uuid=player_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        try:
            record = self.connectorDB.getByUuid(player_uuid)
        except ValueError as e:
            return {'response': str(e)}, 400
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': record}, 200

    def show_with_password_hash_by_username(self, player_username):
        try:
            record = self.connectorDB.getWithPasswordHashByUsername(player_username)
        except ValueError as e:
            return {'response': str(e)}, 400
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': record}, 200

    def show_by_username(self, player_username):
        try:
            record = self.connectorDB.getByUsername(player_username)
        except ValueError as e:
            return {'response': str(e)}, 400
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': record}, 200

    def modify_by_uuid(self, player_uuid):
        if request.headers.get('Content-Type') != 'application/json':
            return {'response': 'Content-type not supported'}, 400

        if (res := PlayerService.check_uuid(player_uuid=player_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        new_username = request.json.get('username')
        new_wallet = request.json.get('wallet')

        if new_wallet and (type(new_wallet) is not int or new_wallet < 0):
            return {'response': f'Invalid wallet'}, 400

        try:
            record = self.connectorDB.update(new_username, new_wallet, player_uuid)
        except ValueError as e:
            return {'response': str(e)}, 400
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': "User updated Successfully!"}, 200

    def create(self):
        if request.headers.get('Content-Type') != 'application/json':
            return {'response': 'Content-type not supported'}, 400

        try:
            username = request.json['username']
            password = request.json['password']
            player_uuid = str(uuid.uuid4())
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

            record = self.connectorDB.add(player_uuid, username, password_hash)
        except KeyError:
            return {'response': 'Missing data'}, 400
        except ValueError as e:
            return {'response': str(e)}, 400
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': record}, 201

    def remove_by_id(self, player_id):
        try:
            self.connectorDB.removeById(player_id)
        except ValueError as e:
            return {'response': str(e)}, 400
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': 'Player deleted'}, 200

    def remove_by_uuid(self, player_uuid):
        if (res := PlayerService.check_uuid(player_uuid=player_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400
        
        try:
            random_name = str(uuid.uuid4()) + 'DELETED'

            self.connectorDB.removeByUuid(player_uuid, random_name)
        except ValueError as e:
            return {'response': str(e)}, 400
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': 'Player deleted'}, 200

    def update_wallet(self, player_uuid):
        if request.headers.get('Content-Type') != 'application/json':
            return {'response': 'Content-type not supported'}, 400

        if (res := PlayerService.check_uuid(player_uuid=player_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        try:
            amount = request.json['amount']

            # amount can be negative (/roll needs to decrement the player wallet)
            if type(amount) is not int:
                return {'response': 'Invalid amount'}, 400

            record = self.connectorDB.updateWallet(player_uuid, amount)
        except KeyError:
            return {'response': 'Missing data'}, 400
        except ValueError as e:
            return {'response': str(e)}, 404
        except Exception as e:
            return {'response': str(e)}, 500

        return jsonify({'response': "wallet updated Successfully!"}), 200

    # static factory methods
    def development(db_name, db_user, db_password, db_host, db_port, db_sslmode, cert_path, key_path):
        db = PlayerConnectorDB(db_name, db_user, db_password, db_host, db_port, db_sslmode)

        PlayerService(db).app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            ssl_context=(cert_path, key_path)
        )

    def testing(cert_path, key_path):
        db = PlayerConnectorDBMock()
        
        PlayerService(db).app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            ssl_context=(cert_path, key_path)
        )

    def production(db_name, db_user, db_password, db_host, db_port, db_sslmode, cert_path, key_path):
        db = PlayerConnectorDB(db_name, db_user, db_password, db_host, db_port, db_sslmode)
        
        PlayerService(db).app.run(
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

    # deployment mode
    DEPLOYMENT_MODE = os.getenv("DEPLOYMENT_MODE")

    match DEPLOYMENT_MODE:
        case 'production':
            PlayerService.production(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, POSTGRES_SSLMODE, CERT_PATH, KEY_PATH)
        case 'testing':
            PlayerService.testing(CERT_PATH, KEY_PATH)
        case 'development':
            PlayerService.development(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, POSTGRES_SSLMODE, CERT_PATH, KEY_PATH)
