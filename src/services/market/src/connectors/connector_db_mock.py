import copy
from datetime import datetime, timezone, timedelta

class MarketConnectorDBMock:
    def __init__(self):
        self.auctions = [
            {
                'uuid': '71520f05-80c5-4cb1-b05a-a9642f9aaaaa',
                'base_price': 200,
                'gacha_uuid': '09907f76-9b0f-4270-84a3-e9780b164ac4',
                'user_uuid': '71520f05-80c5-4cb1-b05a-a9642f9ae111',
                'expired_at': datetime.strptime("12/03/2025 17:20:00+00:00", '%d/%m/%Y %H:%M:%S%z'),
                'closed': False
            },
            {
                'uuid': '71520f05-80c5-4cb1-b05a-a9642f9bbbbb',
                'base_price': 250,
                'gacha_uuid': 'c6cc4f1f-f5f8-4e76-a446-b01b48b10575',
                'user_uuid': '71520f05-80c5-4cb1-b05a-a9642f9ae44d',
                'expired_at': datetime.strptime("07/02/2025 13:31:17+00:00", '%d/%m/%Y %H:%M:%S%z'),
                'closed': False
            },
            {
                'uuid': '71520f05-80c5-4cb1-b05a-a9642f9ccccc',
                'base_price': 250,
                'gacha_uuid': '5721633c-0d52-4742-8aeb-7f0375be39fb',
                'user_uuid': '71520f05-80c5-4cb1-b05a-a9642f9ae44d',
                'expired_at': datetime.strptime("07/02/2025 13:31:17+00:00", '%d/%m/%Y %H:%M:%S%z'),
                'closed': False
            }
        ]

        self.bids = [
            {
                'auction_uuid': '71520f05-80c5-4cb1-b05a-a9642f9aaaaa', 
                'user_uuid': '71520f05-80c5-4cb1-b05a-a9642f9ae44d',
                'offer': 250
            },
            {
                'auction_uuid': '1520f05-80c5-4cb1-b05a-a9642f9bbbbb', 
                'user_uuid': '71520f05-80c5-4cb1-b05a-a9642f9ae111',
                'offer': 300
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


    def getAllAuctions(self):
        return self.auctions

    def getAuctionWithMaxOffer(self, auction_uuid):
        auction = None
        bids = []

        for a in self.auctions:
            if a['uuid'] == auction_uuid:
                auction = a
        
        if not auction:
            raise ValueError('Error: auction not found')

        for b in self.bids:
            if b['auction_uuid'] == auction_uuid:
                bids.append(b)

        offer = 0
        bids = sorted(bids, key=lambda x: x['offer'], reverse=True)
        
        if len(bids) > 0:
            offer = bids[0]['offer']

        auction['offer'] = offer

        return auction

    def getNumberOfActiveAuctionsForGacha(self, player_uuid, gacha_uuid):
        c = 0

        for a in self.auctions:
            if a['gacha_uuid'] == gacha_uuid and not a['closed']:
                c += 1

        return {'active_auctions': c}

    def add(self, auction_uuid, starting_price, gacha_uuid, player_uuid, expired_at):
        for a in self.auctions:
            if a['uuid'] == auction_uuid:
                raise ValueError('Error: failed query')

        auction = {
            'uuid': auction_uuid,
            'base_price': starting_price,
            'gacha_uuid': gacha_uuid,
            'user_uuid': player_uuid,
            'expired_at': expired_at,
            'closed': False
        }

        self.auctions.append(auction)
        return auction

    def makeBid(self, auction_uuid, player_uuid, offer):
        for a in self.auctions:
            if a['uuid'] == auction_uuid:
                bid = {
                    'auction_uuid': auction_uuid, 
                    'user_uuid': player_uuid,
                    'offer': offer
                }

                self.bids.append(bid)

                return

        raise ValueError('Error: auction not found')

    def getAllAuctionsByPlayer(self, player_uuid):
        auctions = []
        for a in self.auctions:
            if a['user_uuid'] == player_uuid:
                auctions.append(a)

        return auctions

    def getAuction(self, auction_uuid):
        for a in self.auctions:
            if a['uuid'] == auction_uuid:
                return a

        raise ValueError('Error: auction not found')

    def getThreeMaxOffersByAuction(self, auction_uuid):
        bids = []
        for b in self.bids:
            if b['auction_uuid'] == auction_uuid:
                bids.append(b)

        bids_with_auction = []
        for a in self.auctions:
            if a['uuid'] == auction_uuid:
                for b in bids:
                    bid_auction = {
                        'owner': a['user_uuid'],
                        'gacha_uuid': a['gacha_uuid'],
                        'closed': a['closed'],
                        'buyer': b['user_uuid'],
                        'offer': b['offer']
                    }

                    bids_with_auction.append(bid_auction)

        return sorted(bids_with_auction, key=lambda x: x['offer'], reverse=True)[:3]

    def closeAndClearBids(self, auction_uuid):
        for i, b in enumerate(self.bids):
            if b['auction_uuid'] == auction_uuid:
                del self.bids[i]

        for a in self.auctions:
            if a['uuid'] == auction_uuid:
                a['closed'] = True
                
                return

        raise ValueError('Error: auction not found')