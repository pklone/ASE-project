import uuid

class CollectionConnectorDBMock:
    # APIs
    def getAll(self):
        return [{
            "description": f"placeholder{i}", 
            "id": i, 
            "image_path": f"placeholder{i}", 
            "name": f"placeholder{i}", 
            "rarity": "C", 
            "quantity": 1,
            "uuid": str(uuid.uuid4())
        } for i in range(1, 3)]

    def getByUuid(self, gacha_uuid):
        return {
            "description": "placeholder", 
            "id": 1, 
            "image_path": "placeholder", 
            "name": "placeholder", 
            "rarity": "C", 
            "uuid": gacha_uuid
        }

    def getByPlayer(self, player_uuid):
        return [{
            "description": "placeholder2", 
            "id": 2, 
            "image_path": "placeholder2", 
            "name": "placeholder2", 
            "rarity": "C", 
            "quantity": 1,
            "uuid": str(uuid.uuid4())
        }]

    def remove(self, gacha_uuid):
        pass

    def updateQuantity(self, gacha_uuid, player_uuid, q):
        pass

    def getAllRarity(self):
        return [{
            "uuid": str(uuid.uuid4()),
            "percentage": 20
        }]

    def getAllByRarity(self, rarity_uuid):
        return [{
            "uuid": str(uuid.uuid4())
        } for _ in range(0, 4)]

    def getRarityBySymbol(self, symbol):
        return {
            "uuid": str(uuid.uuid4())
        }

    def add(self, uuid, name, description, image_path, rarity_uuid):
        pass

    def update(self, new_name, new_description, new_image_path, new_rarity_uuid, gacha_uuid):
        pass
