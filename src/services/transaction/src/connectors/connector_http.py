import requests
import pybreaker

class TransactionConnectorHTTP:
    URL_GET_AUCTION_BY_UUID = 'https://market_service:5000/market/{auction_uuid}'
    URL_GET_ALL_AUCTIONS_BY_PLAYER = 'https://market_service:5000/market/user/{player_uuid}'

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

        return {'http_code': r.status_code, 'json': r.json()}

    # HTTP requests
    def getAuctionByUuid(self, auction_uuid):
        url = TransactionConnectorHTTP.URL_GET_AUCTION_BY_UUID.format(auction_uuid=auction_uuid)
        headers = {
            'Accept': 'application/json',
        }

        return self.__req(requests.get, url, headers=headers)

    def getAllAuctionsByPlayer(self, player_uuid):
        url = TransactionConnectorHTTP.URL_GET_ALL_AUCTIONS_BY_PLAYER.format(player_uuid=player_uuid)

        return self.__req(requests.get, url)

        