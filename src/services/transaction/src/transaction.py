from flask import Flask, request, jsonify, json, abort
from datetime import datetime, timezone
import psycopg2
import psycopg2.extras
import requests
import os
import uuid
import re
import werkzeug.exceptions
from functools import wraps
from connectors.connector_db import TransactionConnectorDB
from connectors.connector_db_mock import TransactionConnectorDBMock
from connectors.connector_http import TransactionConnectorHTTP
from connectors.connector_http_mock import TransactionConnectorHTTPMock

# testing
#   curl -X GET -k https://127.0.0.1:8087
#   curl -X GET -k https://127.0.0.1:8087/uuid/86d1f0db-85c6-48be-9136-71921ec79cf1
#   curl -X GET -k https://127.0.0.1:8087/user/71520f05-80c5-4cb1-b05a-a9642f9ae333
#   curl -X GET -k https://127.0.0.1:8087/user/71520f05-80c5-4cb1-b05a-a9642f9ae333/96cef223-5fd4-4b8d-be62-cfe5dd5fb11b

class TransactionService:
    UUID_REGEX = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

    def __init__(self, connectorHTTP, connectorDB):
        self.app = Flask(__name__)
        self.__init_routes()
        self.connectorDB = connectorDB
        self.connectorHTTP = connectorHTTP

    # routes
    def __init_routes(self):
        self.app.add_url_rule('/',                                                    endpoint='show_all',         view_func=self.show_all,         methods=['GET'])
        self.app.add_url_rule('/',                                                    endpoint='create',           view_func=self.create,           methods=['POST'])
        self.app.add_url_rule('/uuid/<string:transaction_uuid>',                      endpoint='show_by_uuid',     view_func=self.show_by_uuid,     methods=['GET'])
        self.app.add_url_rule('/user/<string:player_uuid>',                           endpoint='show_all_by_user', view_func=self.show_all_by_user, methods=['GET'])
        self.app.add_url_rule('/user/<string:player_uuid>/<string:transaction_uuid>', endpoint='show_by_user',     view_func=self.show_by_user,     methods=['GET'])
        self.app.register_error_handler(werkzeug.exceptions.NotFound, TransactionService.page_not_found)

    # util functions
    def page_not_found(error):
        return {'response': "page not found"}, 404

    def check_uuid(**kwargs):
        res = {'name': None}
        p = re.compile(TransactionService.UUID_REGEX, re.IGNORECASE)

        for key, value in kwargs.items():
            if p.match(value) is None:
                res['name'] = key
                break

        return res

    # decorators
    #def check_uuid(f):
        #@wraps(f)
        #def decorated_function(*args, **kwargs):
        #    p = re.compile(args[0].UUID_REGEX, re.IGNORECASE)
        #
        #    for key, value in kwargs.items():
        #        if 'uuid' in key and p.match(value) is None:
        #                return {'response': f'invalid API uuid'}, 400
        #
        #    return f(*args, **kwargs)
        #
        #return decorated_function

    # APIs
    def show_all(self):
        try:
            records = self.connectorDB.getAll()
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': records}, 200

    def create(self):
        if request.headers.get('Content-Type') != 'application/json':
            return {'response': 'Content-type not supported'}, 400

        try:
            uuid_player = request.json['uuid_player']
            uuid_auction = request.json['uuid_auction']
            price = request.json['price']

            if (res := TransactionService.check_uuid(uuid_player=uuid_player, uuid_auction=uuid_auction)['name']):
                return {'response': f'Invalid {res}'}, 400

            if type(price) is not int or price < 0:
                return {'response': 'Invalid price'}, 400
        except KeyError:
            return {'response': 'Missing data'}, 400

        created_at = int(datetime.now(tz=timezone.utc).timestamp())
        uuid_transaction = str(uuid.uuid4())

        try:
            record = self.connectorDB.add(uuid_transaction, price, created_at, uuid_player, uuid_auction)
        except psycopg2.Error as e:
            return {'response': str(e)}, 500

        return {'response': record}, 201

    def show_by_uuid(self, transaction_uuid):
        if (res := TransactionService.check_uuid(transaction_uuid=transaction_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400
        
        try:
            record = self.connectorDB.getByUuid(transaction_uuid)
        except ValueError as e:
            return {'response': str(e)}, 400
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': record}, 200

    def show_all_by_user(self, player_uuid):
        transactions = []
        transactions_in = []
        transactions_out = []

        auth_header = request.headers.get('Authorization')

        if (res := TransactionService.check_uuid(player_uuid=player_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        # get all the transactions by player_uuid (i.e. the player bought a gacha)
        try:
            records = self.connectorDB.getAllByPlayer(player_uuid)
        except Exception as e:
            return {'response': str(e)}, 500

        # from each transaction, get the related auction
        for record in records:
            try:
                r = self.connectorHTTP.getAuctionByUuid(record['uuid_auction'])

                if r['http_code'] != 200:
                    return {'response': 'Try later'}, 500
            except Exception as e:
                return {'response': str(e)}, 500

            if 'response' in r['json']:
                to_player = r['json']['response']['Player']['uuid']
        
                # mix all the data for out_transaction
                transaction = {
                    'id': record['id'],
                    'uuid': record['uuid'],
                    'price': record['price'],
                    'created_at': record['created_at'],
                    'bought': player_uuid,
                    'sold': to_player,
                    'uuid_auction': record['uuid_auction']
                }

                transactions_out.append(transaction)

        # get all the auctions by player_uuid (i.e. the player sold a gacha)
        try:
            r = self.connectorHTTP.getAllAuctionsByPlayer(player_uuid)
            
            if r['http_code'] != 200:
                return {'response': 'Try later'}, 500
        except Exception as e:
            return {'response': str(e)}, 500   

        # from each auction, get the related auction
        if 'response' in r['json']:
            for auction in r['json']['response']:
                try:
                    record = self.connectorDB.getByAuction(auction['uuid'])
                    r = self.connectorHTTP.getAuctionByUuid(record['uuid_auction'])

                    if r['http_code'] != 200:
                        return {'response': 'Try later'}, 500
                except ValueError as e:
                    # if the auction is not associated with a transaction 
                    # (the auction is still open), we can simply ignore it
                    continue
                    
                    #return {'response': str(e)}, 400
                except Exception as e:
                    return {'response': str(e)}, 500

                if 'response' in r['json']:
                    to_player = r['json']['response']['Player']['uuid']

                # mix all the data for in_transaction
                transaction = {
                    'id': record['id'],
                    'uuid': record['uuid'],
                    'price': record['price'],
                    'created_at': record['created_at'],
                    'bought': to_player,
                    'sold': record['uuid_player'],
                    'uuid_auction': record['uuid_auction']
                }

                transactions_in.append(transaction)

        # in and out transactions
        transactions = {
            "incoming transactions": transactions_in,
            "outgoing transactions": transactions_out
        }

        return {'response': transactions}, 200

    def show_by_user(self, player_uuid, transaction_uuid):
        if (res := TransactionService.check_uuid(player_uuid=player_uuid, transaction_uuid=transaction_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        try:
            record = self.connectorDB.getByUuidAndPlayer(player_uuid, transaction_uuid)
        except ValueError as e:
            return {'response': str(e)}, 400
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': record}, 200

    # static factory methods
    def development(db_name, db_user, db_password, db_host, db_port, db_sslmode, cert_path, key_path):
        db = TransactionConnectorDB(db_name, db_user, db_password, db_host, db_port, db_sslmode)
        http = TransactionConnectorHTTP()

        TransactionService(http, db).app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            ssl_context=(cert_path, key_path)
        )

    def testing(cert_path, key_path):
        db = TransactionConnectorDBMock()
        http = TransactionConnectorHTTPMock()
        
        TransactionService(http, db).app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            ssl_context=(cert_path, key_path)
        )

    def production(db_name, db_user, db_password, db_host, db_port, db_sslmode, cert_path, key_path):
        db = TransactionConnectorDB(db_name, db_user, db_password, db_host, db_port, db_sslmode)
        http = TransactionConnectorHTTP()

        TransactionService(http, db).app.run(
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
            TransactionService.production(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, POSTGRES_SSLMODE, CERT_PATH, KEY_PATH)
        case 'testing':
            TransactionService.testing(CERT_PATH, KEY_PATH)
        case 'development':
            TransactionService.development(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, POSTGRES_SSLMODE, CERT_PATH, KEY_PATH)