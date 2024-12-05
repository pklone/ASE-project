class AuthenticationConnectorHTTPMock:

    def __init__(self):
        
        self.players = [
            {
                "player_username": "test",
                "password_hash": "$2b$12$Z93LSBi0EVtyqVWnZB7tPu8ksgXbrFPd8YjI1haMzGl7KBLrbaR6G",
                "uuid": "71520f05-80c5-4cb1-b05a-a9642f9ae44d",
                "active": True
            },
            {
                "player_username": "test2",
                "password_hash": "$2b$12$Z93LSBi0EVtyqVWnZB7tPu8ksgXbrFPd8YjI1haMzGl7KBLrbaR6G",
                "uuid": "71520f05-80c5-4cb1-b05a-a9642f9ae111",
                "active": False
            }
        ]
    
    def getPlayerWithPasswordHashByUsername(self, player_username):
            
            for player in self.players:
                if player['player_username'] == player_username:
                    return {'http_code': 200, 'http_body': {'response': player}}
            
            raise ValueError('Invalid credentials')