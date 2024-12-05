from datetime import datetime, timezone

class TransactionConnectorDBMock:
    def __init__(self):
        self.transactions = [
            {
                "uuid": "186894c0-9dd3-4222-97a3-d8619135abad",
                "price": 20,
                "created_at": int(datetime.now(tz=timezone.utc).timestamp()),
                "uuid_player": "71520f05-80c5-4cb1-b05a-a9642f9ae44d",      
                "uuid_auction": "71520f05-80c5-4cb1-b05a-a9642f9aaaaa"
            },
            {
                "uuid": "e3c17850-37fa-4011-b43b-2ce1c441d281",
                "price": 100,
                "created_at": int(datetime.now(tz=timezone.utc).timestamp()),
                "uuid_player": "771520f0-80c5-4cb1-b05a-a9642f9ae111",      
                "uuid_auction": "71520f05-80c5-4cb1-b05a-a9642f9bbbbb"
            }
        ]

    # APIs
    def getAll(self):
        return self.transactions

    def add(self, uuid_transaction, price, created_at, uuid_player, uuid_auction):
        for transaction in self.transactions:
            if transaction['uuid_auction'] == uuid_auction:
                raise ValueError('Error: transaction already exists for this auction')

        new_transaction = {
            'uuid': uuid_transaction,
            'price': price,
            'created_at': created_at,
            'uuid_player': uuid_player,
            'uuid_auction': uuid_auction
        }

        self.transactions.append(new_transaction)
        return transaction

    def getByUuid(self, transaction_uuid):
        for transaction in self.transactions:
            if transaction['uuid'] == transaction_uuid:
                return transaction

        raise ValueError('Error: transaction not found')
    
    def getAllByPlayer(self, player_uuid):
        player_transactions = []

        for transaction in self.transactions:
            if transaction['uuid_player'] == player_uuid:
                player_transactions.append(transaction)

        return player_transactions

    def getByAuction(self, auction_uuid):
        for transaction in self.transactions:
            if transaction['uuid_auction'] == auction_uuid:
                return transaction

        raise ValueError('Error: transaction not found')

    def getByUuidAndPlayer(self, player_uuid, transaction_uuid):
        for transaction in self.transactions:
            if transaction['uuid'] == transaction_uuid and transaction['uuid_player'] == player_uuid:
                return transaction

        raise ValueError('Error: transaction not found')