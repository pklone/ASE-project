import requests
import pybreaker

class CurrencyConnectorHTTP:
    URL_PLAYER_ADD_WALLET = 'https://player_service:5000/{player_uuid}/wallet'

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
    def playerWallet(self, player_uuid, amount):
        url = self.URL_PLAYER_ADD_WALLET.format(player_uuid=player_uuid)
        data = {
            'amount' : amount
        }

        return self.__req(requests.put, url, data)