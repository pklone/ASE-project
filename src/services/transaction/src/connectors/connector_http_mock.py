from datetime import datetime, timezone
import copy

class TransactionConnectorHTTPMock:
    def __init__(self):
        self.auctions = [
            {
                'uuid': '71520f05-80c5-4cb1-b05a-a9642f9aaaaa',
                'base_price': 200,
                'gacha_uuid': '09907f76-9b0f-4270-84a3-e9780b164ac4',
                'user_uuid': '771520f05-80c5-4cb1-b05a-a9642f9ae11c',
                'expired_at': int(datetime.now(tz=timezone.utc).timestamp()),
                'closed': False
            },
            {
                'uuid': '71520f05-80c5-4cb1-b05a-a9642f9bbbbb',
                'base_price': 250,
                'gacha_uuid': 'c6cc4f1f-f5f8-4e76-a446-b01b48b10575',
                'user_uuid': '71520f05-80c5-4cb1-b05a-a9642f9ae44d',
                'expired_at': int(datetime.now(tz=timezone.utc).timestamp()),
                'closed': False
            }
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
                'uuid': '771520f05-80c5-4cb1-b05a-a9642f9ae11c', 
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

    def getAuctionByUuid(self, auction_uuid):
        auction = None
        gacha_info = None
        player_info = None

        for a in self.auctions:
            if a['uuid'] == auction_uuid:
                auction = a

        if not auction:
            return {'http_code': 400, 'json': {'response': 'Error: auction not found'}}

        for g in self.gachas:
            if g['uuid'] == auction['gacha_uuid']:
                gacha_info = g

        for r in self.rarities:
            if r['uuid'] == gacha_info['uuid_rarity']:
                tmp = copy.deepcopy(gacha_info)
                tmp['rarity'] = r['name']
                gacha_info = tmp

        for p in self.players:
            if p['uuid'] == auction['user_uuid']:
                player_info = {k: p[k] for k in p if k in ['uuid', 'username']}

        auction = {
            'auction_uuid': auction['uuid'],
            'base_price': auction['base_price'],
            'Gacha': gacha_info, 
            'Player': player_info,
            'expired_at': auction['expired_at'],
            'closed': auction['closed'],
            'actual_offer': 0
        }

        return {'http_code': 200, 'json': {'response': auction}}
        
    def getAllAuctionsByPlayer(self, player_uuid):
        player_auctions = []

        for auction in self.auctions:
            if auction['user_uuid'] == player_uuid:
                player_auctions.append(auction)

        return {'http_code': 200, 'json': {'response': player_auctions}}