import uuid
import copy
from datetime import datetime, timezone

class AccountConnectorHTTPMock:
    def __init__(self):
        self.gacha_player = [
            {
                "uuid_gacha": "5721633c-0d52-4742-8aeb-7f0375be39fb",
                "uuid_player": "c6cc4f1f-f5f8-4e76-a446-b01b48b10575",
                "quantity": 1
            },
            {
                "uuid_gacha": "09907f76-9b0f-4270-84a3-e9780b164ac4",
                "uuid_player": "71520f05-80c5-4cb1-b05a-a9642f9ae44d",
                "quantity": 2
            },
        ]

        self.players = [
            {
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

        self.rarities = [
            {
                "uuid": "ccb1f1a9-9d97-4b3e-8db7-d51d16698ef6",
                "name": "Common",
                "symbol": "C",
                "percentage": 50
            },
            {
                "uuid": "7c0bcf1f-dbf6-4e33-a6e6-e051a54fed4e",
                "name": "Uncommon",
                "symbol": "U",
                "percentage": 30
            }
        ]

        self.gachas = [
            {
                "description": "descr",
                "image_path": "/path",
                "name": "name",
                "uuid_rarity": 'ccb1f1a9-9d97-4b3e-8db7-d51d16698ef6',
                "uuid": "c6cc4f1f-f5f8-4e76-a446-b01b48b10575",
                "active": True
            },
            {
                "description": "descr1",
                "image_path": "/path1",
                "name": "name1",
                "uuid_rarity":  "ccb1f1a9-9d97-4b3e-8db7-d51d16698ef6",
                "uuid": "09907f76-9b0f-4270-84a3-e9780b164ac4",
                "active": True
            },
            {
                "description": "descr2",
                "image_path": "/path2",
                "name": "name1",
                "uuid_rarity":  "7c0bcf1f-dbf6-4e33-a6e6-e051a54fed4e",
                "uuid": "5721633c-0d52-4742-8aeb-7f0375be39fb",
                "active": True
            }
        ]

        self.transactions = [
            {
                "uuid": "186894c0-9dd3-4222-97a3-d8619135abad",
                "price": 20,
                "created_at": int(datetime.now(tz=timezone.utc).timestamp()),
                "uuid_player": "c6cc4f1f-f5f8-4e76-a446-b01b48b10575",      
                "uuid_auction": "71520f05-80c5-4cb1-b05a-a9642f9aaaaa"
            },
            {
                "uuid": "e3c17850-37fa-4011-b43b-2ce1c441d281",
                "price": 100,
                "created_at": int(datetime.now(tz=timezone.utc).timestamp()),
                "uuid_player": "71520f05-80c5-4cb1-b05a-a9642f9ae111",      
                "uuid_auction": "71520f05-80c5-4cb1-b05a-a9642f9bbbbb"
            }
        ]

        self.auctions = [
            {
                'uuid': '71520f05-80c5-4cb1-b05a-a9642f9aaaaa',
                'base_price': 200,
                'gacha_uuid': '09907f76-9b0f-4270-84a3-e9780b164ac4',
                'user_uuid': '71520f05-80c5-4cb1-b05a-a9642f9ae111',
                'expired_at': "12/03/2025 17:20:00+00:00",
                'closed': False
            },
            {
                'uuid': '71520f05-80c5-4cb1-b05a-a9642f9bbbbb',
                'base_price': 250,
                'gacha_uuid': 'c6cc4f1f-f5f8-4e76-a446-b01b48b10575',
                'user_uuid': '71520f05-80c5-4cb1-b05a-a9642f9ae44d',
                'expired_at': "07/02/2025 13:31:17+00:00",
                'closed': False
            },
            {
                'uuid': '71520f05-80c5-4cb1-b05a-a9642f9ccccc',
                'base_price': 250,
                'gacha_uuid': '5721633c-0d52-4742-8aeb-7f0375be39fb',
                'user_uuid': '71520f05-80c5-4cb1-b05a-a9642f9ae44d',
                'expired_at': "07/02/2025 13:31:17+00:00",
                'closed': False
            }
        ]

    def __getPlayerWithoutPasswordHash(self, player):
        return {
            'uuid': player['uuid'], 
            'username': player['username'], 
            'wallet': player['wallet'], 
            'active': player['active']
        }

    def createPlayer(self, username, password):
        for player in self.players:
            if player['username'] == username:
                return {'http_code': 400, 'http_body': {'response': 'Error: player already exists'}}

        new_player = {
            'uuid': str(uuid.uuid4()),
            'username': username,
            'password_hash': password,
            'wallet': 0
        }

        self.players.append(new_player)

        return {'http_code': 200, 'http_body': {'response': new_player}}

    def removePlayer(self, player_uuid):
        for p in self.players:
            if p['uuid'] == player_uuid:
                p['active'] = False
                p['wallet'] = 0
                p['username'] = str(uuid.uuid4()) + 'DELETED'

                return {'http_code': 200, 'http_body': {'response': 'Player deleted'}}
        
        return {'http_code': 400, 'http_body': {'response': 'Error: player not found'}}

    def modifyPlayer(self, player_uuid, username, wallet):
        for player in self.players:
            if player['uuid'] == player_uuid:
                player['username'] = (username or player['username'])
                player['wallet'] = (wallet or player['wallet'])

                return {'http_code': 200, 'http_body': {'response': "User updated Successfully!"}}

        return {'http_code': 400, 'http_body': {'response': 'Error: player not found'}}        

    def playerCollection(self, player_uuid):
        gachas = []

        for gp in self.gacha_player:
            if gp['uuid_player'] == player_uuid:
                for g in self.gachas:
                    if g['uuid'] == gp['uuid_gacha']:
                        tmp = copy.deepcopy(g)
                        tmp['quantity'] = gp['quantity']

                        for r in self.rarities:
                            if tmp['uuid_rarity'] == r['uuid']:
                                tmp['rarity'] = r['name']
                                break

                        gachas.append(tmp)

        return {'http_code': 200, 'http_body': {'response': gachas}}

    def getPlayer(self, player_uuid):
        for p in self.players:
            if p['uuid'] == player_uuid:
                return {'http_code': 200, 'http_body': {'response': p}}

        return {'http_code': 400, 'http_body': {'response': 'Error: player not found'}}

    def getAllTransactions(self, player_uuid):
        transactions = []

        for t in self.transactions:
            if t['uuid_player'] == player_uuid:
                transactions.append(t)

        return {'http_code': 200, 'http_body': {'response': transactions}}

    def getTransaction(self, player_uuid, transaction_uuid):
        for t in self.transactions:
            if t['uuid'] == transaction_uuid and t['uuid_player'] == player_uuid:
                return {'http_code': 200, 'http_body': {'response': t}}

        return {'http_code': 200, 'http_body': {'response': 'Error: transaction not found'}}

    def getAllAuctions(self):
        auctions = []

        for a in self.auctions:
            auction = copy.deepcopy(a)

            for p in self.players:
                if p['uuid'] == auction['user_uuid']:
                    auction['Player'] = {'uuid': p['uuid']}
                    auctions.append(auction)
                    break

        return {'http_code': 200, 'http_body': {'response': auctions}}