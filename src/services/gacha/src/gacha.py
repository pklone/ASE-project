from flask import Flask, request, json, render_template
import os
import jwt
import random
import uuid
import requests
from werkzeug.utils import secure_filename
import werkzeug.exceptions
from functools import wraps
from connectors.connector_db import CollectionConnectorDB
from connectors.connector_db_mock import CollectionConnectorDBMock
from connectors.connector_http import CollectionConnectorHTTP
from connectors.connector_http_mock import CollectionConnectorHTTPMock

# testing
#   curl -X GET -H 'Accept: application/json' -k https://127.0.0.1:8082/collection
#   curl -X GET -k https://127.0.0.1:8082/collection/dde21dde-5513-46d2-8d03-686fc620394c
#   curl -X GET -k https://127.0.0.1:8082/collection/user/71520f05-80c5-4cb1-b05a-a9642f9ae44d
#   curl -X PUT -H 'Content-type: application/json' -d '{"gacha_uuid": "dde21dde-5513-46d2-8d03-686fc620394c", "q": 1}' -k https://127.0.0.1:8082/collection/user/71520f05-80c5-4cb1-b05a-a9642f9ae44d
#   curl -X POST -H 'Content-Type: application/json' -d '{"username": "test", "password": "test"}' -c cookie.jar -k https://127.0.0.1:8081/login
#       curl -X GET -H 'Accept: application/json' -k -b cookie.jar https://127.0.0.1:8082/roll
#   cp ~/Documenti/media/immagini/meme/batkek.jpg . 
#       curl -X POST -F 'gacha_image=@batkek.jpg' -F 'name=placeholder' -F 'description=placeholder' -F 'rarity=S' -k https://127.0.0.1:8082/collection
#   cp ~/Documenti/media/immagini/meme/9b5.png . 
#       curl -X PUT -F 'gacha_image=@9b5.png' -F 'name=placeholder2' -F 'description=placeholder2' -F 'rarity=S' -k https://127.0.0.1:8082/collection/069fa2c5-a6a0-487d-b533-96acc3a6e538
#   curl -X DELETE -k https://127.0.0.1:8082/collection/9743e615-42ba-46f3-8ec4-155cb6ef86f7

class CollectionService:
    UPLOAD_FOLDER = './static/images/gachas'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    STATIC_DIR_PATH = '/assets'
    GACHAS_DIR_PATH = STATIC_DIR_PATH + '/images/gachas'

    def __init__(self, connectorHTTP, connectorDB, jwt_secret):
        self.app = Flask(__name__, static_url_path=self.STATIC_DIR_PATH)
        self.app.config['UPLOAD_FOLDER'] = self.UPLOAD_FOLDER
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000  # 16 MB

        self.__init_routes()
        self.connectorHTTP = connectorHTTP
        self.connectorDB = connectorDB
        self.jwt_secret = jwt_secret

    # routes
    def __init_routes(self):
        self.app.add_url_rule('/collection',                           endpoint='show_all',        view_func=self.show_all,        methods=['GET'])
        self.app.add_url_rule('/collection/<string:gacha_uuid>',       endpoint='show',            view_func=self.show,            methods=['GET'])
        self.app.add_url_rule('/collection/user/<string:player_uuid>', endpoint='show_by_player',  view_func=self.show_by_player,  methods=['GET'])
        self.app.add_url_rule('/collection/user/<string:player_uuid>', endpoint='update_quantity', view_func=self.update_quantity, methods=['PUT'])
        self.app.add_url_rule('/roll',                                 endpoint='roll',            view_func=self.roll,            methods=['GET'])
        self.app.add_url_rule('/collection',                           endpoint='add_gacha',       view_func=self.add_gacha,       methods=['POST'])
        self.app.add_url_rule('/collection/<string:gacha_uuid>',       endpoint='modify_gacha',    view_func=self.modify_gacha,    methods=['PUT'])
        self.app.add_url_rule('/collection/<string:gacha_uuid>',       endpoint='delete_gacha',    view_func=self.delete_gacha,    methods=['DELETE'])
        self.app.register_error_handler(werkzeug.exceptions.NotFound, self.page_not_found)

    # util functions
    def page_not_found(self, error):
        return {'response': "page not found"}, 404

    def allowed_file(self, filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

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
            
            if decoded_jwt['scope'] != 'player':
                return {'response': 'You are not autorized'}, 401 

            additional = {'auth_uuid': decoded_jwt['sub']}

            return f(*args, **kwargs, **additional)

        return decorated_function

    # APIs
    def show_all(self):
        try:
            records = self.connectorDB.getAll()
        except Exception as e:
            return {'response': str(e)}, 500

        if 'application/json' in request.headers['Accept']:
            return {'response': records}, 200
        elif 'text/html' in request.headers['Accept']:
            return render_template('collection.html', records=records), 200
        else:
            return {'response': 'Not supported'}, 400

    def show(self, gacha_uuid):
        try:
            record = self.connectorDB.getByUuid(gacha_uuid)
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': record}, 200

    def show_by_player(self, player_uuid):
        try:
            records = self.connectorDB.getByPlayer(player_uuid)
        except Exception as e:
            return {'response': str(e)}, 500

        return {'response': records}, 200

    def update_quantity(self, player_uuid):
        try:
            q = request.json['q'] # q is 1 (buyer) or -1 (owner)
            gacha_uuid = request.json['gacha_uuid']

            self.connectorDB.updateQuantity(gacha_uuid, player_uuid, q)
        except KeyError:
            return {'message': 'Missing data'}
        except Exception as e:
            return {'response': str(e)}, 500
        
        return {'response': 'success'}, 200

    @login_required
    def roll(self, auth_uuid):
        try:
            records = self.connectorDB.getAllRarity()
        except Exception as e:
            return {'response': str(e)}, 500

        percentages = [x['percentage'] for x in records]
        weights = [x['uuid'] for x in records]

        rarity_uuid = random.choices(weights, percentages)[0]

        try:
            records = self.connectorDB.getAllByRarity(rarity_uuid)
        except Exception as e:
            return {'response': str(e)}, 500

        gacha_uuid = random.choice([x['uuid'] for x in records])

        try:
            r = self.connectorHTTP.updatePlayerWallet(auth_uuid, -10)
            if r['http_code'] != 200:
                return {'response': 'No money available'}, 400

            self.connectorDB.updateQuantity(gacha_uuid, auth_uuid, 1)
            record = self.connectorDB.getByUuid(gacha_uuid)
        except Exception as e:
            return {'response': str(e)}, 500

        if 'application/json' in request.headers.get('Accept'):
            return {'response': record}, 200
        elif 'text/html' in request.headers.get('Accept'):
            return render_template("roll.html"), 200
        else:
            return {'response': 'Not supported'}, 400

    def add_gacha(self):
        if 'gacha_image' not in request.files:
            return {'response': 'gacha image not found'}, 400

        file = request.files['gacha_image']
        if file.filename == '':
            return {'response': 'filename not found'}, 400

        if not file or not self.allowed_file(file.filename):
            return {'response': 'invalid image format or empty image'}, 400

        try:
            name = request.form['name']
            description = request.form['description']
            rarity = request.form['rarity']

            record = self.connectorDB.getRarityBySymbol(rarity)
            if not record:
                return {'response': 'invalid rarity'}, 400

            filename = secure_filename(file.filename)
            destination_path = os.path.join(self.UPLOAD_FOLDER, filename)
            file.save(destination_path)

            gacha_uuid = str(uuid.uuid4())
            rarity_uuid = record['uuid']
            image_path = os.path.join(self.GACHAS_DIR_PATH, filename)

            record = self.connectorDB.add(gacha_uuid, name, description, image_path, rarity_uuid)
        except KeyError:
            return {'response': 'Missing data'}, 400
        except FileNotFoundError:
            return {'response': 'Internal error'}, 500
        except Exception as e:
            return {'response': str(e)}, 500
        
        return {'response': record}, 201
        
    def modify_gacha(self, gacha_uuid):
        new_name = request.form.get('name')
        new_description = request.form.get('description')
        new_rarity = request.form.get('rarity')
        
        new_image_path = None
        new_rarity_uuid = None

        if new_rarity:
            try:
                record = self.connectorDB.getRarityBySymbol(new_rarity)
                if not record:
                    return {'response': 'invalid rarity'}, 400

                new_rarity_uuid = record['uuid']
            except Exception as e:
                return {'response': str(e)}, 500
        
        if 'gacha_image' in request.files:
            file = request.files['gacha_image']

            if file.filename == '':
                return {'response': 'gacha image filename not found'}, 400

            if not file or not self.allowed_file(file.filename):
                return {'response': 'invalid image format or empty image'}, 400
            
            try:
                filename = secure_filename(file.filename)
                destination_path = os.path.join(self.UPLOAD_FOLDER, filename)
                file.save(destination_path)

                new_image_path = os.path.join(self.GACHAS_DIR_PATH, filename)
            except FileNotFoundError:
                return {'response': 'Internal error'}, 500

        try:
            record = self.connectorDB.update(new_name, new_description, new_image_path, new_rarity_uuid, gacha_uuid)
        except Exception as e:
            return {'response': str(e)}, 500
        
        return {'response': record}, 200

    def delete_gacha(self, gacha_uuid):
        try:
            self.connectorDB.remove(gacha_uuid)
        except Exception as e:
            return {'response': str(e)}, 500
        
        return {'response': 'Gacha deleted'}, 200

    # static factory methods
    def development(db_name, db_user, db_password, db_host, db_port, db_sslmode, cert_path, key_path, jwt_secret):
        db = CollectionConnectorDB(db_name, db_user, db_password, db_host, db_port, db_sslmode)
        http = CollectionConnectorHTTP()

        CollectionService(http, db, jwt_secret).app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            ssl_context=(cert_path, key_path)
        )

    def testing(cert_path, key_path, jwt_secret):
        db = CollectionConnectorDBMock()
        http = CollectionConnectorHTTPMock()
        
        CollectionService(http, db, jwt_secret).app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            ssl_context=(cert_path, key_path)
        )

    def production(db_name, db_user, db_password, db_host, db_port, db_sslmode, cert_path, key_path, jwt_secret):
        db = CollectionConnectorDB(db_name, db_user, db_password, db_host, db_port, db_sslmode)
        http = CollectionConnectorHTTP()
        
        CollectionService(http, db, jwt_secret).app.run(
            host="0.0.0.0", 
            port=5000, 
            ssl_context=(cert_path, key_path)
        )
        ssl_context=(CERT_PATH, KEY_PATH)

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
            CollectionService.production(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, POSTGRES_SSLMODE, CERT_PATH, KEY_PATH, JWT_SECRET)
        case 'testing':
            CollectionService.testing(CERT_PATH, KEY_PATH, JWT_SECRET)
        case 'development':
            CollectionService.development(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, POSTGRES_SSLMODE, CERT_PATH, KEY_PATH, JWT_SECRET)