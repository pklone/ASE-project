import requests
import pybreaker

class MarketConnectorHTTP:
    URL_COLLECTION_SERVICE    = 'https://gacha_service:5000/collection'
    URL_PLAYER_SERVICE_UUID   = 'https://player_service:5000/uuid/{player_uuid}'
    URL_GACHA_SERVICE_UUID    = 'https://gacha_service:5000/collection/{gacha_uuid}'
    URL_PLAYER_COLLECTION     = 'https://gacha_service:5000/collection/user/{player_uuid}'
    URL_TRANSACTION_SERVICE   = 'https://transaction_service:5000'
    URL_PLAYER_WALLET         = 'https://player_service:5000/{player_uuid}/wallet'

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
    def getAllGachas(self):
        url = MarketConnectorHTTP.URL_COLLECTION_SERVICE
        headers={
            'Accept': 'application/json'
        }

        return self.__req(requests.get, url, headers=headers)

    def getGacha(self, gacha_uuid):
        url = MarketConnectorHTTP.URL_GACHA_SERVICE_UUID.format(gacha_uuid=gacha_uuid)
        headers = {
            'Accept': 'application/json'
        }

        return self.__req(requests.get, url, headers=headers)

    def getPlayer(self, player_uuid):
        url = MarketConnectorHTTP.URL_PLAYER_SERVICE_UUID.format(player_uuid=player_uuid)
        headers = {
            'Accept': 'application/json'
        }

        return self.__req(requests.get, url, headers=headers)

    def getPlayerCollection(self, player_uuid):
        url = MarketConnectorHTTP.URL_PLAYER_COLLECTION.format(player_uuid=player_uuid)

        return self.__req(requests.get, url, headers=headers)

    def createTransaction(self, buyer_uuid, auction_uuid, offer):
        url = MarketConnectorHTTP.URL_TRANSACTION_SERVICE
        data = {
                'uuid_player': buyer_uuid,
                'uuid_auction': auction_uuid,
                'price': offer
        }
        
        return self.__req(requests.post, url, data)

    def updatePlayerWallet(self, player_uuid, amount):
        url = MarketConnectorHTTP.URL_PLAYER_WALLET.format(player_uuid=player_uuid)
        data = {
            'amount': amount
        }
        
        return self.__req(requests.put, url, data)
    