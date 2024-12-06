import requests
import pybreaker

#except json.JSONDecodeError as e:
#return jsonify({'response': 'Json error'}), 500

class AuthenticationConnectorHTTP:
    URL_GET_WITH_PASSWORD_BY_USERNAME = 'https://player_service:5000/username/{player_username}/all' # nosec B105 Not leaking any password here just using it to get the player with the password hash

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
    def getPlayerWithPasswordHashByUsername(self, player_username):
        url = AuthenticationConnectorHTTP.URL_GET_WITH_PASSWORD_BY_USERNAME.format(player_username=player_username)

        return self.__req(requests.get, url)