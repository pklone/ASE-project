
rarity = [
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

gacha = [
    {
        "description": "descr",
        "image_path": "/path",
        "name": "name",
        "rarity": rarity[0],
        "uuid": "a0f0f673-595d-445f-bbf5-be68217f5dab",
        "active": True
    },
    {
        "description": "descr1",
        "image_path": "/path1",
        "name": "name1",
        "rarity":  rarity[1],
        "uuid": "c685eae6-a473-4bca-a5c8-b710bb495ca6",
        "active": True
    },
    {
        "description": "descr2",
        "image_path": "/path2",
        "name": "name1",
        "rarity":  rarity[1],
        "uuid": "5721633c-0d52-4742-8aeb-7f0375be39fb",
        "active": True
    }
]

players = [ 
    {
        "uuid_player": "4d8ecfb4-c58f-4a9b-9f35-f28ee49834ef",
        "gachas": [{"quantity": 2, "gacha": gacha[0]}, 
                  {"quantity": 1, "gacha": gacha[1]}]
    },
    {
        "uuid_player": "8fa6f80d-fbf3-4d06-a0db-86dfe126117f",
        "gachas": {"quantity": 1, "gacha": gacha[1]}
    }
]


class CollectionConnectorDBMock:
    # APIs
    def getAll(self):

        transformed_gacha = [
            {**item, "rarity": item["rarity"]["name"]}
            for item in gacha
        ]       

        return transformed_gacha

    def getByUuid(self, gacha_uuid):

        transformed_gacha = [
        {**item, "rarity": item["rarity"]["name"]}
        for item in gacha
        ]       
        
        gacha_item = next((g for g in transformed_gacha if g["uuid"] == gacha_uuid), None)
        if not gacha_item:
            raise ValueError(f'Error: gacha not found')
        return gacha_item

    def getByPlayer(self, player_uuid):

        player_gachas = next((p for p in players if p["uuid_player"] == player_uuid), None)
        if not player_gachas:
            return []
        
        gachas = player_gachas["gachas"]
        
        transformed_gacha = [
         {
              **item["gacha"],
              "rarity": item["gacha"]["rarity"]["name"],
              "quantity": item["quantity"]
         }
         for item in gachas
        ] 

        return transformed_gacha

    def updateQuantity(self, gacha_uuid, player_uuid, q):
        
        player_gachas = next((p for p in players if p["uuid_player"] == player_uuid), None)
        if not player_gachas:
            raise ValueError(f'Error: player not found')

        gachas = player_gachas["gachas"]
        gacha_item = next((g for g in gachas if g["gacha"]["uuid"] == gacha_uuid), None)
        if not gacha_item:
            gacha_new = next((g for g in gacha if g["uuid"] == gacha_uuid), None)
            if not gacha_new:
                raise ValueError(f'Error: gacha not found')
            player_gachas["gachas"].append({"quantity": q, "gacha": gacha_new})
            return True                
        
        gacha_item["quantity"] = gacha_item["quantity"] + q

        return True

    def getAllRarity(self):
        
        transformed_rarity = [
            { "uuid": item["uuid"], "percentage": item["percentage"]}
            for item in rarity
        ]

        return transformed_rarity

    def getAllByRarity(self, rarity_uuid):

        rarity_item = next((r for r in rarity if r["uuid"] == rarity_uuid), None)
        if not rarity_item:
            raise ValueError(f'Error: rarity not found')
        
        gachas = [g for g in gacha if g["rarity"]["uuid"] == rarity_uuid and g["active"] == True]

        return gachas

    def getRarityBySymbol(self, symbol):
        
        rarity_item = next((r for r in rarity if r["symbol"] == symbol), None)
        if not rarity_item:
            raise ValueError(f'Error: rarity not found')
        return {"uuid": rarity_item["uuid"]}

    def add(self, uuid, name, description, image_path, rarity_uuid):

        if next((g for g in gacha if g["name"] == name), None):
            raise ValueError(f'Error: gacha already exists')
        
        rarity_item = next((r for r in rarity if r["uuid"] == rarity_uuid), None)
        
        new_gacha = {
            "description": description,
            "image_path": image_path,
            "name": name,
            "rarity": rarity_item,
            "uuid": uuid
        }

        gacha.append(new_gacha)

        return new_gacha

    def update(self, new_name, new_description, new_image_path, new_rarity_uuid, gacha_uuid):
        
        gacha_item = next((g for g in gacha if g["uuid"] == gacha_uuid), None)
        if not gacha_item:
            raise ValueError(f'Error: gacha not found')
        
        # modify that specific gacha in the list
        gacha_item["name"] = new_name
        gacha_item["description"] = new_description
        gacha_item["image_path"] = new_image_path
        gacha_item["rarity"] = next((r for r in rarity if r["uuid"] == new_rarity_uuid), None)

        return gacha_item

    def remove(self, gacha_uuid):
        
        gacha_item = next((g for g in gacha if g["uuid"] == gacha_uuid), None)
        if not gacha_item:
            raise ValueError(f'Error: gacha not found')
        
        gacha_item["active"] = False

        return 
