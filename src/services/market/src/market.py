from flask import Flask, request, jsonify, json, render_template
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from functools import wraps
import socket
import os
import uuid
import jwt
import re
from mytasks import add, req, invoke_payment
import werkzeug.exceptions
from connectors.connector_db import MarketConnectorDB
from connectors.connector_db_mock import MarketConnectorDBMock
from connectors.connector_http import MarketConnectorHTTP
from connectors.connector_http_mock import MarketConnectorHTTPMock

# testing
#   curl -X GET -H @headers.txt -H 'Accept: application/json' -k https://127.0.0.1:8086/market

class MarketService:
    UUID_REGEX = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

    def __init__(self, connectorHTTP, connectorDB, jwt_secret):
        self.app = Flask(__name__)

        self.__init_routes()
        self.connectorHTTP = connectorHTTP
        self.connectorDB = connectorDB
        self.jwt_secret = jwt_secret

    # routes
    def __init_routes(self):
        self.app.add_url_rule('/market',                               endpoint='show_all',            view_func=self.show_all,            methods=['GET'])
        self.app.add_url_rule('/market/<string:auction_uuid>',         endpoint='show_one',            view_func=self.show_one,            methods=['GET'])
        self.app.add_url_rule('/market/gacha/<string:gacha_uuid>',     endpoint='show_create_auction', view_func=self.show_create_auction, methods=['GET'])
        self.app.add_url_rule('/market',                               endpoint='create_auction',      view_func=self.create_auction,      methods=['POST'])
        self.app.add_url_rule('/market/<string:auction_uuid>/bid',     endpoint='make_bid',            view_func=self.make_bid,            methods=['POST'])
        self.app.add_url_rule('/market/<string:auction_uuid>/close',   endpoint='close_auction',       view_func=self.close_auction,       methods=['PUT'])
        self.app.add_url_rule('/market/<string:auction_uuid>/payment', endpoint='payment',             view_func=self.payment,             methods=['POST'])
        self.app.add_url_rule('/market/user/<string:player_uuid>',     endpoint='show_user_auctions',  view_func=self.show_user_auctions,  methods=['GET'])
        self.app.register_error_handler(werkzeug.exceptions.NotFound, MarketService.page_not_found)

    # util functions
    def page_not_found(error):
        return {'response': "page not found"}, 404

    def check_uuid(**kwargs):
        res = {'name': None}
        p = re.compile(MarketService.UUID_REGEX, re.IGNORECASE)

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
                return {'response': 'You are not autorized'}, 401
        
            additional = {'auth_uuid': decoded_jwt['sub']}
        
            return f(*args, **kwargs, **additional)
        
        return decorated_function

    @login_required
    def show_all(self, auth_uuid):
        auctions = []
        is_admin = False

        try:
            hostname = (socket.gethostbyaddr(request.remote_addr)[0]).split('.')[0]
        except socket.herror:
            hostname = 'testing-from-127.0.0.1'
            #return {'response': 'unknown host'}, 500

        if hostname == 'admin_service':
            is_admin = True

        try:
            records = self.connectorDB.getAllAuctions()
            r = self.connectorHTTP.getAllGachas()

            gachas = {x['uuid']: x for x in r['http_body']['response']}

            # iterate over all the auctions list
            for record in records:
                r = self.connectorHTTP.getPlayer(record['user_uuid'])
                player_info = {k: r['http_body']['response'][k] for k in r['http_body']['response'] if k in ['uuid', 'username']}

                if record['gacha_uuid'] in gachas:
                    gacha_info = gachas[record['gacha_uuid']]

                    expire_utc = datetime.strptime(record['expired_at'], '%d/%m/%Y %H:%M:%S%z')
                    expire = expire_utc.astimezone(ZoneInfo('Europe/Rome'))

                    auction = {
                        'auction_uuid': record['uuid'],
                        'base_price': record['base_price'],
                        'Gacha': gacha_info, 
                        'Player': player_info,
                        'expired_at': expire.strftime('%d/%m/%Y %H:%M:%S %Z'),
                        'closed': record['closed']
                    }
                    
                    # the player can see only open auctions, 
                    # whereas the admin can see also the closed ones
                    if not is_admin:
                        if record['closed'] == False:
                            auctions.append(auction)
                    else:
                        auctions.append(auction)
        except ValueError as e:
            return {'response': str(e)}, 500

        if 'application/json' in request.headers.get('Accept'):
            return {'response': auctions}, 200
        elif 'text/html' in request.headers.get('Accept'):
            return render_template("marketplace.html", auctions=auctions), 200
        else:
            return {'response': 'Not supported'}, 400

    @login_required
    def show_one(self, auction_uuid, auth_uuid):
        is_admin = False

        try:
            hostname = (socket.gethostbyaddr(request.remote_addr)[0]).split('.')[0]    
        except socket.herror:
            hostname = 'testing-from-127.0.0.1'
            #return {'response': 'unknown host'}, 500

        if hostname == 'admin_service' or hostname == 'transaction_service':
            is_admin = True

        if (res := MarketService.check_uuid(auction_uuid=auction_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        try:
            record = self.connectorDB.getAuctionWithMaxOffer(auction_uuid)

            if not is_admin and record['closed'] == True:
                return {'response': 'Auction is closed'}, 200 

            r = self.connectorHTTP.getGacha(record['gacha_uuid'])
            gacha_info = r['http_body']['response']

            r = self.connectorHTTP.getPlayer(record["user_uuid"])
            player_info = {k: r['http_body']['response'][k] for k in r['http_body']['response'] if k in ['uuid', 'username']}
        except ValueError as e:
            return {'response': str(e)}, 400 
        except Exception as e:
            return {'response': str(e)}

        auction = {
            'auction_uuid': record['uuid'],
            'base_price': record['base_price'],
            'Gacha': gacha_info, 
            'Player': player_info,
            'expired_at': record['expired_at'],
            'closed': record['closed'],
            'actual_offer': record['offer']
        }
                
        if 'application/json' in request.headers.get('Accept'):
            return {'response': auction}, 200
        elif 'text/html' in request.headers.get('Accept'):
            return render_template("auction_details.html", auction=auction), 200
        else:
            return {'response': 'Not supported'}, 400
    
    @login_required
    def show_create_auction(self, gacha_uuid, auth_uuid):
        if (res := MarketService.check_uuid(gacha_uuid=gacha_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        return render_template("create_auction.html", gacha_uuid=gacha_uuid), 200

    @login_required
    def create_auction(self, auth_uuid):
        try:
            gacha_uuid = request.json['gacha_uuid']
            starting_price = int(request.json['starting_price'])

            if starting_price <= 0:
                return {'response': 'Starting price must be positive'}, 400

            r = self.connectorHTTP.getPlayerCollection(auth_uuid)
            gachas = r['http_body']['response']
            
            player_gacha = None
            for gacha in gachas:
                if gacha['uuid'] == gacha_uuid:
                    player_gacha = gacha
                    break

            if not player_gacha or player_gacha['quantity'] < 1:
                return {'response': 'You don\'t have this gacha'}, 400

            record = self.connectorDB.getNumberOfActiveAuctionsForGacha(auth_uuid, gacha_uuid)

            if player_gacha['quantity'] <= record['active_auctions']:
                return {'response': f'You have only {player_gacha['quantity']} copies of gacha {player_gacha["name"]}'}, 400

            auction_uuid = str(uuid.uuid4())
            expired_at = datetime.now(tz=timezone.utc) + timedelta(seconds=60*5)

            record = self.connectorDB.add(auction_uuid, starting_price, gacha_uuid, auth_uuid, expired_at)
        except KeyError:
            return {'response': 'Missing data'}, 400
        except Exception as e:
            return {'response': str(e)}, 500

        task = invoke_payment.apply_async((auction_uuid,), eta=expired_at)
        
        if 'application/json' in request.headers.get('Accept'):
            return {'response': record}, 201
        elif 'text/html' in request.headers.get('Accept'):
            return render_template("create_auction.html", success=True), 201
        else:
            return {'response': 'Not supported'}, 400

    @login_required
    def make_bid(self, auction_uuid, auth_uuid):
        if (res := MarketService.check_uuid(auction_uuid=auction_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        try:
            offer = int(request.json['offer'])

            if offer <= 0:
                return {'response': 'Bid must be positive'}, 400

            record = self.connectorHTTP.getAuctionWithMaxOffer(auction_uuid)

            current_time = int(datetime.now(tz=timezone.utc).timestamp())
            final_time = int(record['expired_at'].timestamp())
            base_price = record['base_price']
            current_price = record['offer']

            if auth_uuid == record['user_uuid']:
                return {'response': 'You\'re the owner of this auction'}, 400

            if final_time <= current_time:
                return {'response': 'Auction is closed'}, 400
            
            if offer <= base_price:
                return {'response': 'Offer must be higher than base price'}, 400
            
            if offer <= current_price:
                return {'response': 'Offer must be higher than current price'}, 400

            self.connectorDB.makeBid(auction_uuid, auth_uuid, offer)
        except KeyError:
            return {'response': 'Missing data'}, 400
        except ValueError as e:
            return {'response': str(e)}, 400
        except Exception as e:
            return {'response': str(e)}, 500

        auction = {
            'auction_uuid': auction_uuid, 
            'player_uuid': auth_uuid, 
            'offer': offer, 
            'closed': record['closed']
        }
        
        return {'response': auction}, 200

    @login_required
    def close_auction(self, auction_uuid, auth_uuid):
        player_uuid = None
        is_admin = False

        try:
            hostname = (socket.gethostbyaddr(request.remote_addr)[0]).split('.')[0]    
        except socket.herror:
            return {'response': 'unknown host'}, 500

        if hostname == 'admin_service':
            is_admin = True

        if (res := MarketService.check_uuid(auction_uuid=auction_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        try:
            record = self.connectorDB.getAuctionWithMaxOffer(auction_uuid)

            if record['closed'] == True:
                return {'response': 'Auction is already closed'}, 400

            if not is_admin:
                if record['user_uuid'] != auth_uuid:
                    return {'response': 'You\'re not the owner of this auction'}, 400

                if record['offer'] != 0:
                    return {'response': 'Not possible to close an auction with bids'}, 400

            self.connectorDB.close(auction_uuid)
        except ValueError as e:
            return {'response': str(e)}, 400
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': 'Auction closed'}, 200

    def payment(self, auction_uuid):
        try:
            hostname = (socket.gethostbyaddr(request.remote_addr)[0]).split('.')[0]    
        except socket.herror:
            return {'response': 'unknown host'}, 500
        
        if 'celery_worker' not in hostname and 'admin_service' not in hostname:
            return {'response': 'You\'re not authorized'}, 403
        
        if (res := MarketService.check_uuid(auction_uuid=auction_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        try:
            record = self.connectorDB.getAuction(auction_uuid)

            if record['closed'] == True:
                return {'response': 'Auction is already closed'}, 400

            records = self.connectorDB.getThreeMaxOffersByAuction(auction_uuid)

            if len(records) == 0 or (records[0]['offer'] == 0 and records[1]['offer'] == 0 and records[2]['offer'] == 0):
                return {'response': 'There are no bids for this auction'}, 400

            for i in range(min(3, len(records))):
                buyer_uuid = record[i]['buyer']
                owner_uuid = record[i]['owner']
                offer = record[i]['offer']

                r = self.connectorHTTP.getPlayer(buyer_uuid)
                if r['http_code'] != 200:
                    return {'response': 'invalid user'}, r['http_code']

                buyer_data = r['http_body']['response']

                if buyer_data['wallet'] < offer:
                    continue

                r = self.connectorHTTP.createTransaction(buyer_uuid, auction_uuid, offer)
                if r['http_code'] != 201:
                    return {'response': 'Failed to create transaction'}, r['http_code']
                
                r = self.connectorHTTP.updatePlayerWallet(buyer_uuid, -offer)
                if r['http_code'] != 200:
                    return {'response': 'Failed to update buyer wallet'}, 500

                r = self.connectorHTTP.updatePlayerWallet(owner_uuid, offer)
                if r['http_code'] != 200:
                    return {'response': 'Failed to update owner wallet'}, 500

                r = self.connectorHTTP.updatePlayerCollection(buyer_uuid, record[i]['gacha_uuid'], 1)
                if r['http_code'] != 200:
                    return {'response': 'Failed to update buyer collection'}, 500

                r = self.connectorHTTP.updatePlayerCollection(owner_uuid, record[i]['gacha_uuid'], -1)
                if r['http_code'] != 200:
                    return {'response': 'Failed to update owner collection'}, 500

                self.connectorDB.closeAndClearBids(auction_uuid)

                transaction_data = {
                    'uuid_player': buyer_uuid,
                    'uuid_auction': auction_uuid,
                    'price': offer
                }

                return {'response': 'Transaction completed', 'transaction': transaction_data}, 200

            return {'response': 'No buyers with sufficient funds'}, 200
        except ValueError as e:
            return {'response': str(e)}, 400
        except Exception as e:
            return {'response': str(e)}, 500

    @login_required
    def show_user_auctions(self, player_uuid, auth_uuid):
        try:
            hostname = (socket.gethostbyaddr(request.remote_addr)[0]).split('.')[0]  

            if hostname != 'admin_service' and hostname != 'transaction_service':
                return {'response': 'Forbidden'}, 403
        except socket.herror:
            return {'response': 'unknown host'}, 500

        if (res := MarketService.check_uuid(player_uuid=player_uuid)['name']):
            return {'response': f'Invalid {res}'}, 400

        try:
            records = self.connectorDB.getAllAuctionsByPlayer(player_uuid)
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': records}, 200

    # static factory methods
    def development(db_name, db_user, db_password, db_host, db_port, db_sslmode, cert_path, key_path, jwt_secret):
        db = MarketConnectorDB(db_name, db_user, db_password, db_host, db_port, db_sslmode)
        http = MarketConnectorHTTP()

        MarketService(http, db, jwt_secret).app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            ssl_context=(cert_path, key_path)
        )

    def testing(cert_path, key_path, jwt_secret):
        db = MarketConnectorDBMock()
        http = MarketConnectorHTTPMock()
        
        MarketService(http, db, jwt_secret).app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            ssl_context=(cert_path, key_path)
        )

    def production(db_name, db_user, db_password, db_host, db_port, db_sslmode, cert_path, key_path, jwt_secret):
        db = MarketConnectorDB(db_name, db_user, db_password, db_host, db_port, db_sslmode)
        http = MarketConnectorHTTP()
        
        MarketService(http, db, jwt_secret).app.run(
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
            MarketService.production(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, POSTGRES_SSLMODE, CERT_PATH, KEY_PATH, JWT_SECRET)
        case 'testing':
            MarketService.testing(CERT_PATH, KEY_PATH, JWT_SECRET)
        case 'development':
            MarketService.development(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, POSTGRES_SSLMODE, CERT_PATH, KEY_PATH, JWT_SECRET)
