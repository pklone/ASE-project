import requests
import pybreaker

class AdminConnectorHTTP:
    URL_ADMIN_LOGIN             = 'https://authentication_service:5000/admin_login'
    URL_PLAYER_SERVICE_ROOT     = 'https://player_service:5000'
    URL_PLAYER_SERVICE_UUID     = 'https://player_service:5000/uuid/{player_uuid}'
    URL_USER_COLLECTION         = 'https://gacha_service:5000/collection/user/{player_uuid}'
    URL_COLLECTION_SERVICE      = 'https://gacha_service:5000/collection'
    URL_COLLECTION_SERVICE_UUID = 'https://gacha_service:5000/collection/{gacha_uuid}'
    URL_MARKET_SERVICE          = 'https://market_service:5000/market'
    URL_MARKET_SERVICE_UUID     = 'https://market_service:5000/market/{auction_uuid}'
    URL_AUCTION_CLOSE           = 'https://market_service:5000/market/{auction_uuid}/close'
    URL_PLAYER_TRANSACTIONS     = 'https://transaction_service:5000/user/{player_uuid}'
    URL_aUCTION_PAYMENT         = 'https://market_service:5000/market/{auction_uuid}/payment'

    def __init__(self):
        self.circuitbreaker = pybreaker.CircuitBreaker(
            fail_max=5, 
            reset_timeout=60*5
        )

    def __req(self, requests_func, url, data=None, json=None, headers=None, files=None, verify=False):
        try:
            r = self.circuitbreaker.call(requests_func, url=url, verify=verify, headers=headers, data=data, json=json, files=files)
        except Exception as e:
            raise Exception("Error: connection error")

        return {'http_code': r.status_code, 'http_body': r.json(), 'http_headers': r.headers}

    # HTTP requests
    def adminLogin(self, username, password):
        url = AdminConnectorHTTP.URL_ADMIN_LOGIN
        json = {
            'username': username,
            'password': password
        }

        return self.__req(requests.post, url, json=json)

    def getAllPlayers(self):
        url = AdminConnectorHTTP.URL_PLAYER_SERVICE_ROOT

        return self.__req(requests.get, url)

    def getPlayer(self, player_uuid):
        url = AdminConnectorHTTP.URL_PLAYER_SERVICE_UUID.format(player_uuid=player_uuid)

        return self.__req(requests.get, url)

    def modifyPlayer(self, player_uuid, username, wallet):
        url = AdminConnectorHTTP.URL_PLAYER_SERVICE_UUID.format(player_uuid=player_uuid)
        json = {
            'username': username,
            'wallet': wallet
        }
        
        return self.__req(requests.put, url, json=json)

    def removePlayer(self, player_uuid):
        url = AdminConnectorHTTP.URL_PLAYER_SERVICE_UUID.format(player_uuid=player_uuid)

        return self.__req(requests.delete, url)

    def getPlayerCollection(self, player_uuid):
        url = AdminConnectorHTTP.URL_USER_COLLECTION.format(player_uuid=player_uuid)

        return self.__req(requests.get, url)

    def addGacha(self, name, description, rarity, gacha_file):
        url = AdminConnectorHTTP.URL_COLLECTION_SERVICE
        data = {
            'name': name,
            'description': description,
            'rarity': rarity
        }

        files = {
            'gacha_image': (gacha_file.filename, gacha_file.stream, gacha_file.mimetype)
        }

        return self.__req(requests.post, url, data=data, files=files)

    def modifyGacha(self, gacha_uuid, name, description, rarity, gacha_file):
        url = AdminConnectorHTTP.URL_COLLECTION_SERVICE_UUID.format(gacha_uuid=gacha_uuid)
        data = {
            'name': name,
            'description': description,
            'rarity': rarity
        }

        files = {
            'gacha_image': (gacha_file.filename, gacha_file.stream, gacha_file.mimetype)
        }

        return self.__req(requests.put, url, data=data, files=files)
    
    def removeGacha(self, gacha_uuid):
        url = AdminConnectorHTTP.URL_COLLECTION_SERVICE_UUID.format(gacha_uuid=gacha_uuid)

        return self.__req(requests.delete, url)

    def getAllAuctions(self, auth_header):
        url = AdminConnectorHTTP.URL_MARKET_SERVICE
        headers = {
            'Accept': 'application/json',
            'Authorization': auth_header
        }

        return self.__req(requests.get, url, headers=headers)

    def getAuction(self, auth_header, auction_uuid):
        url = AdminConnectorHTTP.URL_MARKET_SERVICE_UUID.format(auction_uuid=auction_uuid)
        headers = {
            'Accept': 'application/json',
            'Authorization': auth_header
        }

        return self.__req(requests.get, url, headers=headers)

    def closeAuction(self, auth_header, auction_uuid):
        url = AdminConnectorHTTP.URL_AUCTION_CLOSE.format(auction_uuid=auction_uuid)
        headers = {
            'Authorization': auth_header
        }

        return self.__req(requests.put, url, headers=headers)

    def getAllPlayerTransactions(self, auth_header, player_uuid):
        url = AdminConnectorHTTP.URL_PLAYER_TRANSACTIONS.format(player_uuid=player_uuid)
        headers = {
            'Authorization': auth_header
        }

        return self.__req(requests.get, url, headers=headers)

    def paymentAuction(self, auction_uuid):
        url = AdminConnectorHTTP.URL_AUCTION_PAYMENT.format(auction_uuid=auction_uuid)

        return self.__req(requests.post, url)
