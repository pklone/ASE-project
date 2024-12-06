import copy
import uuid
from datetime import datetime, timezone

class MarketConnectorHTTPMock:
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
                "username": "test",
                "uuid": "71520f05-80c5-4cb1-b05a-a9642f9ae111",
                "wallet": 500,
                "active": True
            },
            {
                "username": "test3",
                "uuid": "71520f05-80c5-4cb1-b05a-a9642f9ae44d",
                "wallet": 500,
                "active": True
            },
            {
                "username": "test2",
                "uuid": "c6cc4f1f-f5f8-4e76-a446-b01b48b10575",
                "wallet": 500,
                "active": False
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

    def getAllGachas(self):
        gachas = copy.deepcopy(self.gachas)

        for g in gachas:
            for r in self.rarities:
                if r['uuid'] == g['uuid_rarity']:
                    g['rarity'] = r['name']

        return {'http_code': 200, 'http_body': {'response': gachas}}

    def getGacha(self, gacha_uuid):
        for g in self.gachas:
            if g['uuid'] == gacha_uuid:
                return {'http_code': 200, 'http_body': {'response': g}}

        return {'http_code': 400, 'http_body': {'response': 'Error: player not found'}}
        
    def getPlayer(self, player_uuid):
        for p in self.players:
            if p['uuid'] == player_uuid:
                return {'http_code': 200, 'http_body': {'response': p}}

        return {'http_code': 400, 'http_body': {'response': 'Error: player not found'}}

    def getPlayerCollection(self, player_uuid):
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

    def createTransaction(self, buyer_uuid, auction_uuid, offer):
        for t in self.transactions:
            if t['uuid_auction'] == auction_uuid:
                return {'http_code': 400, 'http_body': {'response': 'Error: transaction already exists for this auction'}}

        new_transaction = {
            'uuid': str(uuid.uuid4()),
            'price': offer,
            'created_at': int(datetime.now(tz=timezone.utc).timestamp()),
            'uuid_player': buyer_uuid,
            'uuid_auction': auction_uuid
        }

        self.transactions.append(new_transaction)
        
        return {'http_code': 200, 'http_body': {'response': new_transaction}}

    def updatePlayerWallet(self, player_uuid, amount):
        for p in self.players:
            if p['uuid'] == player_uuid:
                p['wallet'] += amount
                return {'http_code': 200, 'http_body': {'response': p}}

        return {'http_code': 404, 'http_body': {'response': 'Error: player not found'}}

    def updatePlayerCollection(self, player_uuid, gacha_uuid, q):
        for gp in self.gacha_player:
            if gp['uuid_player'] == gacha_uuid and gp['uuid_player'] == gacha_uuid:
                gp['quantity'] += amount

        return {'http_code': 200, 'http_body': {'response': 'success'}}