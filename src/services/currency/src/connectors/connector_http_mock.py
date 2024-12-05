class CurrencyConnectorHTTPMock:
    def playerWallet(self, player_uuid, purchase):
        response = {
            'http_code': 200,
            'http_body': {"response": "wallet updated Successfully!"}
        }
        return {'http_code': response['http_code'], "http_body": response['http_body']}