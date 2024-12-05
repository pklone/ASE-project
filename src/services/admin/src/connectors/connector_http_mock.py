import uuid
from werkzeug.utils import secure_filename
import os

class AdminConnectorHTTPMock:

    STATIC_DIR_PATH = '/assets'
    GACHAS_DIR_PATH = STATIC_DIR_PATH + '/images/gachas'

    def __init__(self):
        
        self.token = {
               "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2FzZS5sb2NhbGhvc3QiLCJzdWIiOiIxZTc4NWE1ZGQtN2ZkZC00ODNmLTkzYjMtYjg0ZWNhYTYyNjgzIiwiZXhwIjoxNzMzNDE3NDM0LCJzY29wZSI6ImFkbWluIn0.ldKk_LxX84BMROMklXtBDsP1tm8MKCX2KnFHmaG8tLI",
               "expires_in": 3600,
               "id_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2FzZS5sb2NhbGhvc3QiLCJhdWQiOiJodHRwczovL2FzZS5sb2NhbGhvc3QvbG9naW4iLCJzdWIiOiIxZTc4NWE1ZGQtN2ZkZC00ODNmLTkzYjMtYjg0ZWNhYTYyNjgzIiwiZXhwIjoxNzMzNDE3NDM0LCJpYXQiOjE3MzM0MTM4MzQsIm5iZiI6MTczMzQxMzgzNCwic2NvcGUiOiJhZG1pbiJ9.gYdJNAohyOLh5VF4Ro8r4YmdOB8mEQGJmnhDoYwxmvE",
               "token_type": "Bearer"
           }
        
        self.users = [
        {
            "active": True,
            "password_hash": "$2b$12$Z93LSBi0EVtyqVWnZB7tPu8ksgXbrFPd8YjI1haMzGl7KBLrbaR6G",
            "username": "test",
            "uuid": "71520f05-80c5-4cb1-b05a-a9642f9ae44d",
            "wallet": 1000
        },
        {
            "active": True,
            "password_hash": "$2b$12$Z93LSBi0EVtyqVWnZB7tPu8ksgXbrFPd8YjI1haMzGl7KBLrbaR6G",
            "username": "test2",
            "uuid": "71520f05-80c5-4cb1-b05a-a9642f9ae111",
            "wallet": 200
        }
        ]

        self.gacha = [
            {
                "description": "descr",
                "image_path": "/path",
                "name": "name",
                "rarity": "Common",
                "uuid": "a0f0f673-595d-445f-bbf5-be68217f5dab",
                "active": True
            },
            {
                "description": "descr1",
                "image_path": "/path1",
                "name": "name1",
                "rarity": "Uncommon",
                "uuid": "c685eae6-a473-4bca-a5c8-b710bb495ca6",
                "active": True
            },
            {
                "description": "descr2",
                "image_path": "/path2",
                "name": "name1",
                "rarity": "Uncommon",
                "uuid": "5721633c-0d52-4742-8aeb-7f0375be39fb",
                "active": True
            }
            ]

        self.collection = [ 
            {
                "uuid_player": "71520f05-80c5-4cb1-b05a-a9642f9ae44d",
                "gachas": [{"quantity": 2, "gacha": self.gacha[0]}, 
                          {"quantity": 1, "gacha": self.gacha[1]}]
            },
            {
                "uuid_player": "71520f05-80c5-4cb1-b05a-a9642f9ae111",
                "gachas": {"quantity": 1, "gacha": self.gacha[1]}
            }
        ]

        self.auctions = [
            {
                "id": 1,
                "uuid": "c502a9c4-6420-4d16-8183-8225576ade53",
                "uuid_player": "71520f05-80c5-4cb1-b05a-a9642f9ae44d",
                "gacha": self.gacha[0],
                "base_price": 100,
                "actual_offer": 500,
                "expired_at": "2021-09-01T00:00:00Z",
                "closed": False
            },
            {
                "id": 2,
                "uuid": "6c666fbf-747e-4ba5-9008-b74f0e3ae8ed",
                "uuid_player": "71520f05-80c5-4cb1-b05a-a9642f9ae44d",
                "gacha": self.gacha[1],
                "base_price": 200,
                "actual_offer": 200,
                "expired_at": "2021-09-01T00:00:00Z",
                "closed": False
            }
        ]
       
        self.transactions = [
            {
                "uuid": "d8e6010d-077d-4474-ad9d-6e324eeef7f1",
                "amount": 700,
                "created_at": 11112011,
                "uuid_player": "71520f05-80c5-4cb1-b05a-a9642f9ae44d"
            },
            {
                "uuid": "d8e6010d-077d-4474-ad9d-6e324eeef7f2",
                "amount": 900,
                "created_at": 11112022,
                "uuid_player": "71520f05-80c5-4cb1-b05a-a9642f9ae44d"
            }
        ]

    def adminLogin(self, username, password):

        admin_token = { "response": self.token }

        return {"http_code": 200, "http_body": admin_token, "http_headers": {}}
    
    def getAllPlayers(self):

        players = {"response": self.users}

        return {"http_code": 200, "http_body": players}
    
    def getPlayer(self, player_uuid):

        player = next((player for player in self.users if player["uuid"] == player_uuid), None)
        if player is None:
            return {"http_code": 400, "http_body": {"response": "Error: Player not found"}}

        return {"http_code": 200, "http_body": {"response": player}}
    
    def modifyPlayer(self, user_uuid, new_username, new_wallet):

        player = next((player for player in self.users if player["uuid"] == user_uuid), None)
        if player is None:
            return {"http_code": 400, "http_body": {"response": "Error: Player not found"}}

        player["username"] = new_username
        player["wallet"] = new_wallet

        return {"http_code": 200, "http_body": {"response": "User updated Successfully!"}}
    
    def removePlayer(self, user_uuid):

        player = next((player for player in self.users if player["uuid"] == user_uuid), None)
        if player is None:
            return {"http_code": 400, "http_body": {"response": "Error: Player not found"}}

        self.users.remove(player)

        return {"http_code": 200, "http_body": {"response": "Player deleted"}}
    
    def getPlayerCollection(self, player_uuid):

        player = next((player for player in self.collection if player["uuid_player"] == player_uuid), None)
        if player is None:
            return {"http_code": 400, "http_body": {"response": "Error: Player not found"}}

        return {"http_code": 200, "http_body": {"response": player["gachas"]}}
    
    def addGacha(self, name, description, rarity, file):

        filename = secure_filename(file.filename)
        image_path = os.path.join(self.GACHAS_DIR_PATH, filename)

        if rarity == "C":
            rarity = "Common"
        elif rarity == "U":
            rarity = "Uncommon"

        new_gacha = {
            "description": description,
            "image_path": image_path,
            "name": name,
            "rarity": rarity,
            "uuid": str(uuid.uuid4()),
            "active": True
        }

        self.gacha.append(new_gacha)

        return {"http_code": 201, "http_body": {"response": new_gacha}}
    
    def modifyGacha(self, gacha_uuid, new_name, new_description, new_rarity, new_file):

        filename = secure_filename(new_file.filename)
        new_image_path = os.path.join(self.GACHAS_DIR_PATH, filename)

        gacha_item = next((g for g in self.gacha if g["uuid"] == gacha_uuid), None)
        if gacha_item is None:
            return {"http_code": 400, "http_body": {"response": "Error: Gacha not found"}}

        if new_rarity == "C":
            new_rarity = "Common"
        elif new_rarity == "U":
            new_rarity = "Uncommon"

        gacha_item["name"] = new_name[0]
        gacha_item["description"] = new_description[0]
        gacha_item["image_path"] = new_image_path
        gacha_item["rarity"] = new_rarity

        return {"http_code": 200, "http_body": {"response": gacha_item}}
    
    def removeGacha(self, gacha_uuid):

        gacha_item = next((g for g in self.gacha if g["uuid"] == gacha_uuid), None)
        if gacha_item is None:
            return {"http_code": 400, "http_body": {"response": "Error: Gacha not found"}}

        gacha_item["active"] = False

        return {"http_code": 200, "http_body": {"response": "Gacha deleted"}}
    
    def getAllAuctions(self, auth__uuid):
            
        auction_list = [
            {
                "id": auction["id"],
                "uuid": auction["uuid"],
                "uuid_player": auction["uuid_player"],
                "gacha": auction["gacha"],
                "base_price": auction["base_price"],
                "expired_at": auction["expired_at"],
                "closed": auction["closed"]
            }
            for auction in self.auctions
        ]

        return {"http_code": 200, "http_body": {"response": auction_list}}
    
    def getAuction(self, auth_header, auction_uuid):

        auction = next((auction for auction in self.auctions if auction["uuid"] == auction_uuid), None)
        if auction is None:
            return {"http_code": 400, "http_body": {"response": "Error: Auction not found"}}

        return {"http_code": 200, "http_body": {"response": auction}}
    
    def getAllPlayerTransactions(self, auth_header, user_uuid):
        
        transactions = [transaction for transaction in self.transactions if transaction["uuid_player"] == user_uuid]
        if transactions is None:
            return {"http_code": 400, "http_body": []}

        return {"http_code": 200, "http_body": {"response": transactions}}

    def closeAuction(self, auth_header, auction_uuid):

        auction = next((auction for auction in self.auctions if auction["uuid"] == auction_uuid), None)
        if auction is None:
            return {"http_code": 400, "http_body": {"response": "Error: Auction not found"}}
        
        if auction["closed"]:
            return {"http_code": 400, "http_body": {"response": "Auction is already closed"}}

        auction["closed"] = True

        return {"http_code": 200, "http_body": {"response": "Auction closed"}}

    def paymentAuction(self, auction_uuid):

        auction = next((auction for auction in self.auctions if auction["uuid"] == auction_uuid), None)
        if auction is None:
            return {"http_code": 400, "http_body": {"response": "Error: Auction not found"}}
        
        if auction["closed"]:
            return {"http_code": 400, "http_body": {"response": "Auction is already closed"}}

        auction["closed"] = True

        new_transaction = {
            "uuid": str(uuid.uuid4()),
            "amount": auction["actual_offer"],
            "created_at": 11112010,
            "uuid_player": "d8e6010d-077d-4474-ad9d-6e324eeef7f2"
        }

        self.transactions.append(new_transaction)

        return {"http_code": 200, "http_body": {"response": {"Transaction completed": new_transaction}}}