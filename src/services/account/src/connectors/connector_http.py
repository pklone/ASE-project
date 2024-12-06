import requests
import pybreaker

class AccountConnectorHTTP:
    URL_PLAYER_SERVICE_ROOT = 'https://player_service:5000'
    URL_PLAYER_SERVICE_UUID = 'https://player_service:5000/uuid/{player_uuid}'
    URL_PLAYER_COLLECTION   = 'https://gacha_service:5000/collection/user/{player_uuid}'
    URL_TRANSACTIONS_PLAYER = 'https://transaction_service:5000/user/{player_uuid}'
    URL_TRANSACTION_PLAYER  = 'https://transaction_service:5000/user/{player_uuid}/{transaction_uuid}'
    URL_MARKET_SERVICE      = 'https://market_service:5000/market'

    def __init__(self):
        self.circuitbreaker = pybreaker.CircuitBreaker(
            fail_max=5, 
            reset_timeout=60*5
        )

    def __req(self, requests_func, url, data=None, headers=None, verify=False):
        try:
            r = self.circuitbreaker.call(requests_func, url=url, verify=verify, headers=headers, json=data)
        except Exception as e:
            raise Exception("Error: connection error")

        return {'http_code': r.status_code, 'http_body': r.json()}

    # HTTP requests
    def createPlayer(self, username, password):
        url = AccountConnectorHTTP.URL_PLAYER_SERVICE_ROOT
        data = {
            'username': username,
            'password': password
        }

        return self.__req(requests.post, url, data)

    def removePlayer(self, player_uuid):
        url = AccountConnectorHTTP.URL_PLAYER_SERVICE_UUID.format(player_uuid=player_uuid)

        return self.__req(requests.delete, url)

    def modifyPlayer(self, player_uuid, username):
        url = AccountConnectorHTTP.URL_PLAYER_SERVICE_UUID.format(player_uuid=player_uuid)
        data = {
            'username': username
        }

        return self.__req(requests.put, url, data)

    def playerCollection(self, player_uuid):
        url = AccountConnectorHTTP.URL_PLAYER_COLLECTION.format(player_uuid=player_uuid)

        return self.__req(requests.get, url)

    def getPlayer(self, player_uuid):
        url = AccountConnectorHTTP.URL_PLAYER_SERVICE_UUID.format(player_uuid=player_uuid)

        return self.__req(requests.get, url)

    def getAllTransactions(self, player_uuid):
        url = AccountConnectorHTTP.URL_TRANSACTIONS_PLAYER.format(player_uuid=player_uuid)

        return self.__req(requests.get, url)

    def getTransaction(self, player_uuid, transaction_uuid):
        url = AccountConnectorHTTP.URL_TRANSACTION_PLAYER.format(player_uuid=player_uuid, transaction_uuid=transaction_uuid)

        return self.__req(requests.get, url)

    def getAllAuctions(self):
        url = AccountConnectorHTTP.URL_MARKET_SERVICE
        headers = {
            'Accept': 'application/json'
        }

        return self.__req(requests.get, url, headers=headers)

