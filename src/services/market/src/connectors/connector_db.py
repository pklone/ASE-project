import psycopg2
import psycopg2.extras

class MarketConnectorDB:
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
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        except psycopg2.Error as e:
            raise Exception('Error: invalid cursor')

        return cursor

    def __close(self):
        try:
            self.conn.close()
        except psycopg2.Error as e:
            raise Exception('Error: cannot close connection')

    # APIs
    def getAllAuctions(self):
        try:
            cursor = self.__cursor()
            cursor.execute('''SELECT id, uuid, base_price, gacha_uuid, user_uuid, to_char(expired_at, 'DD/MM/YYYY HH:MI:SSOF:00') as expired_at, closed from auction''')
            records = cursor.fetchall()
            cursor.close()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return records

    def getAuctionWithMaxOffer(self, auction_uuid):
        try:
            cursor = self.__cursor()
            cursor.execute('''
                SELECT a.uuid, a.base_price, a.gacha_uuid, a.user_uuid, to_char(a.expired_at, 'DD/MM/YYYY HH:MI:SSOF:00') as expired_at, a.closed, COALESCE(b.offer, 0) AS offer
                    FROM auction a 
                    LEFT JOIN bid b ON a.uuid = b.auction_uuid 
                    WHERE a.uuid = %s 
                    ORDER BY b.offer desc limit 1''',
            [auction_uuid])

            if cursor.rowcount == 0:
                raise ValueError('Error: auction not found')

            record = cursor.fetchone()
            cursor.close()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return record

    def getNumberOfActiveAuctionsForGacha(self, player_uuid, gacha_uuid):
        try:
            cursor = self.__cursor()
            cursor.execute('SELECT count(id) as active_auctions FROM auction WHERE user_uuid = %s AND gacha_uuid = %s AND closed = FALSE', 
                [player_uuid, gacha_uuid])
            record = cursor.fetchone()
            cursor.close()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return record

    def add(self, auction_uuid, starting_price, gacha_uuid, player_uuid, expired_at):
        try:
            cursor = self.__cursor()
            cursor.execute('''
                INSERT INTO auction 
                    (id, uuid, base_price, gacha_uuid, user_uuid, expired_at) 
                VALUES 
                    (DEFAULT, %s, %s, %s, %s, %s)''', 
            [auction_uuid, starting_price, gacha_uuid, player_uuid, expired_at])

            cursor.execute('''
                SELECT id, uuid, base_price, gacha_uuid, user_uuid, expired_at 
                FROM auction 
                WHERE uuid = %s''', 
            [auction_uuid])

            if cursor.rowcount == 0:
                self.conn.rollback()
                raise ValueError('Error: failed query')

            record = cursor.fetchone()

            self.conn.commit()
            cursor.close()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception('Error: failed query')

        return record


    def makeBid(self, auction_uuid, player_uuid, offer):
        try:
            cursor = self.__cursor()
            cursor.execute('SELECT 1 FROM auction WHERE uuid = %s',
                [auction_uuid])

            if cursor.rowcount == 0:
                raise ValueError('Error: auction not found')

            cursor.execute('''
                INSERT INTO bid 
                    (id, auction_uuid, user_uuid, offer) 
                VALUES 
                    (DEFAULT, %s, %s, %s)''', 
            [auction_uuid, player_uuid, offer])

            self.conn.commit()
            cursor.close()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception('Error: failed query')

        return

    def getAllAuctionsByPlayer(self, player_uuid):
        try:
            cursor = self.__cursor()
            cursor.execute('''
                SELECT id, uuid, base_price, gacha_uuid, user_uuid, closed,
                       to_char(expired_at, 'DD/MM/YYYY HH:MI:SSOF:00') as expired_at 
                FROM auction
                WHERE user_uuid = %s''', 
            [player_uuid])
            records = cursor.fetchall()
            cursor.close()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return records

    def getAuction(self, auction_uuid):
        try:
            cursor = self.__cursor()
            cursor.execute('''
                SELECT uuid, base_price, gacha_uuid, user_uuid, expired_at, closed
                FROM auction''',
            [auction_uuid])

            if cursor.rowcount == 0:
                raise ValueError('Error: auction not found')

            record = cursor.fetchone()
            cursor.close()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return record


    def getThreeMaxOffersByAuction(self, auction_uuid):
        try:
            cursor = self.__cursor()
            cursor.execute('''
                WITH RankedBids AS (
                    SELECT 
                        a.user_uuid AS owner, 
                        a.gacha_uuid,
                        a.closed,
                        b.user_uuid AS buyer, 
                        COALESCE(b.offer, 0) AS offer
                    FROM auction a
                    LEFT JOIN bid b ON a.uuid = b.auction_uuid
                    WHERE a.uuid = %s
                    ),
                DistinctBuyers AS (
                    SELECT DISTINCT ON (buyer) 
                        owner, 
                        buyer, 
                        gacha_uuid,
                        closed,
                        offer
                    FROM RankedBids
                    WHERE buyer IS NOT NULL
                    ORDER BY buyer, offer DESC
                    )
                SELECT owner, buyer, closed, gacha_uuid, offer
                FROM DistinctBuyers
                ORDER BY offer DESC
                LIMIT 3;
            ''',
            [auction_uuid])
            records = cursor.fetchall()
            cursor.close()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return records

    def closeAndClearBids(self, auction_uuid):
        try:
            cursor = self.__cursor()
            cursor.execute('DELETE FROM bid WHERE auction_uuid = %s',
                [auction_uuid])

            cursor.execute('UPDATE auction SET closed = TRUE WHERE uuid = %s',
                [auction_uuid])

            if cursor.rowcount == 0:
                raise ValueError('Error: auction not found')

            self.conn.commit()
            cursor.close()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception('Error: failed query')

        return 
            


                

                    