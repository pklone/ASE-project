import psycopg2
import psycopg2.extras

class TransactionConnectorDB:
    def __init__(self, db_name, db_user, db_password, db_host, db_port, db_sslmode):
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.db_sslmode = db_sslmode

        self.conn = None
        self.cursor = None

        self.__connect()
        self.__cursor()

    def __del__(self):
        self.__close()

    # util functions
    def __connect(self):
        try:
            #if not self.conn:
            self.conn = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port,
                sslmode=self.db_sslmode
            )
        except psycopg2.Error as e:
            raise Exception('Error: database connection failed')

    def __cursor(self):
        try:
            #if not cursor:
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        except psycopg2.Error as e:
            raise Exception('Error: invalid cursor')

    def __close(self):
        try:
            self.cursor.close()
            self.conn.close()
        except psycopg2.Error as e:
            raise Exception('Error: cannot close connection')

    # APIs
    def getAll(self):
        try:
            self.cursor.execute('SELECT * from transaction')

            records = self.cursor.fetchall()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return records

    def add(self, uuid_transaction, price, created_at, uuid_player, uuid_auction):
        try:
            self.cursor.execute('SELECT 1 FROM transaction WHERE uuid_auction = %s', [uuid_auction])
            if self.cursor.rowcount == 0:
                raise ValueError('Error: transaction already exists for this auction')

            if self.cursor.rowcount == 0:
                self.conn.rollback()
                raise Exception('Error: failed query')

            self.cursor.execute('''
                INSERT INTO transaction 
                    (id, uuid, price, created_at, uuid_player, uuid_auction) 
                VALUES 
                    (DEFAULT, %s, %s, %s, %s, %s)''', 
                [uuid_transaction, price, created_at, uuid_player, uuid_auction])

            self.cursor.execute('''
                SELECT id, uuid, price, created_at, uuid_player, uuid_auction FROM transaction WHERE uuid = %s''', 
                [uuid_transaction])

            if self.cursor.rowcount == 0:
                self.conn.rollback()
                raise Exception('Error: failed query')

            record = self.cursor.fetchone()

            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception('Error: failed query')

        return record

    def getByUuid(self, transaction_uuid):
        try:
            self.cursor.execute('SELECT id, uuid, price, created_at, uuid_player, uuid_auction FROM transaction WHERE uuid = %s', 
                [transaction_uuid])

            if self.cursor.rowcount == 0:
                raise ValueError(f'Error: transaction not found')

            record = self.cursor.fetchone()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return record

    def getAllByPlayer(self, player_uuid):
        try:
            self.cursor.execute('SELECT id, uuid, price, created_at, uuid_player, uuid_auction FROM transaction WHERE uuid_player = %s', 
                [player_uuid])

            records = self.cursor.fetchall()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return records

    def getByAuction(self, auction_uuid):
        try:
            self.cursor.execute('SELECT id, uuid, price, created_at, uuid_player, uuid_auction FROM transaction WHERE uuid_auction = %s', 
                [auction_uuid])

            if self.cursor.rowcount == 0:
                raise ValueError(f'Error: transaction not found')

            record = self.cursor.fetchone()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return record

    def getByUuidAndPlayer(self, player_uuid, transaction_uuid):
        try:
            self.cursor.execute('SELECT id, uuid, price, created_at, uuid_player, uuid_auction FROM transaction WHERE uuid_player = %s AND uuid = %s', 
                [player_uuid, transaction_uuid])

            if self.cursor.rowcount == 0:
                raise ValueError(f'Error: transaction not found')

            record = self.cursor.fetchone()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return record