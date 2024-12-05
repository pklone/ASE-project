class PlayerConnectorDBMock:
    def __init__(self):
        self.players = [{
                'uuid': '71520f05-80c5-4cb1-b05a-a9642f9ae44d', 
                'username': 'test', 
                'password_hash': '$2b$12$Z93LSBi0EVtyqVWnZB7tPu8ksgXbrFPd8YjI1haMzGl7KBLrbaR6G', 
                'wallet': 1000, 
                'active': True
            },
            {
                'uuid': '71520f05-80c5-4cb1-b05a-a9642f9ae111', 
                'username': 'test2', 
                'password_hash': '$2b$12$Z93LSBi0EVtyqVWnZB7tPu8ksgXbrFPd8YjI1haMzGl7KBLrbaR6G', 
                'wallet': 200, 
                'active': True
            }
        ]

    def __getPlayerWithoutPasswordHash(self, player):
        return {
            'uuid': player['uuid'], 
            'username': player['username'], 
            'wallet': player['wallet'], 
            'active': player['active']
        }

    def getAll(self):
        return self.players

    def getByUuid(self, player_uuid):
        for player in self.players:
            if player['uuid'] == player_uuid:
                return self.__getPlayerWithoutPasswordHash(player)

        raise ValueError('Error: player not found')

    def getWithPasswordHashByUsername(self, username):
        for player in self.players:
            if player['username'] == username:
                return player

        raise ValueError('Error: player not found')

    def getByUsername(self, username):
        for player in self.players:
            if player['username'] == username:
                return self.__getPlayerWithoutPasswordHash(player)

        raise ValueError('Error: player not found')

    def add(self, player_uuid, username, password_hash):
        for player in self.players:
            if player['username'] == username:
                raise ValueError('Error: player already exists')

        new_player = {
            'uuid': player_uuid,
            'username': username,
            'password_hash': password_hash,
            'wallet': 0
        }

        self.players.append(new_player)
        return new_player

    def update(self, new_username, new_wallet, player_uuid):
        for player in self.players:
            if player['uuid'] == player_uuid:
                player['username'] = (new_username or player['username'])
                player['wallet'] = (new_wallet or player['wallet'])
                
                return self.__getPlayerWithoutPasswordHash(player)
                
        raise ValueError('Error: player not found')

    def updateWallet(self, player_uuid, amount):
        for player in self.players:
            if player['uuid'] == player_uuid:
                player['wallet'] = player['wallet'] + amount

                return self.__getPlayerWithoutPasswordHash(player)

        raise ValueError('Error: player not found')

    def removeByUuid(self, player_uuid, random_name):
        for player in self.players:
            if player['uuid'] == player_uuid:
                player['active'] = False
                player['wallet'] = 0
                player['username'] = random_name

                return

        raise ValueError('Error: player not found')