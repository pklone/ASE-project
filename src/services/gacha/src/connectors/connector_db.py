import psycopg2
import psycopg2.extras

class CollectionConnectorDB:
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
            self.cursor.execute("""
                SELECT g.uuid, g.name, LEFT(g.description, 100) || '...' AS description, image_path, r.name as rarity 
                FROM gacha g 
                    INNER JOIN rarity r on g.uuid_rarity = r.uuid WHERE g.active = true
            """)

            records = self.cursor.fetchall()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return records

    def getByUuid(self, gacha_uuid):
        try:
            self.cursor.execute("""
                SELECT g.uuid, g.name, description, image_path, r.name as rarity 
                FROM gacha g 
                    INNER JOIN rarity r on g.uuid_rarity = r.uuid WHERE g.uuid = %s
                """, [gacha_uuid])

            if self.cursor.rowcount == 0:
                raise Exception(f'Error: gacha not found')

            record = self.cursor.fetchone()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return record


    def getByPlayer(self, player_uuid):
        try:
            self.cursor.execute("""
                SELECT g.uuid, g.name, LEFT(g.description, 100) || '...' AS description, image_path, quantity, r.name as rarity 
                FROM gacha g 
                    INNER JOIN rarity r on g.uuid_rarity = r.uuid 
                    INNER JOIN player_gacha pg on g.uuid = pg.uuid_gacha 
                WHERE pg.uuid_player = %s""", 
            [player_uuid])

            records = self.cursor.fetchall()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return records

    def remove(self, gacha_uuid):
        try:
            self.cursor.execute("SELECT 1 from gacha WHERE uuid = %s", 
                [gacha_uuid])
            
            if self.cursor.rowcount == 0:
                raise Exception("Error: gacha not found")

            self.cursor.execute("UPDATE gacha SET active = false WHERE uuid = %s", 
                [gacha_uuid])
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception('Error: failed query')

        return

    def updateQuantity(self, gacha_uuid, player_uuid, q):
        try:
            self.cursor.execute('SELECT 1 FROM player_gacha WHERE uuid_player = %s AND uuid_gacha = %s', 
                [player_uuid, gacha_uuid])

            if self.cursor.rowcount == 0:
                self.cursor.execute('INSERT INTO player_gacha (uuid_player, uuid_gacha) VALUES (%s, %s)',
                    [player_uuid, gacha_uuid])
            else:
                self.cursor.execute('UPDATE player_gacha SET quantity = quantity + (%s) WHERE uuid_player = %s AND uuid_gacha = %s', 
                    [q, player_uuid, gacha_uuid])

            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(str(e))

        return

    def getAllRarity(self):
        try:
            self.cursor.execute('SELECT uuid, percentage FROM rarity')
            records = self.cursor.fetchall()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return records

    def getAllByRarity(self, rarity_uuid):
        try:
            self.cursor.execute('SELECT 1 FROM rarity WHERE uuid = %s',
                [rarity_uuid])

            if self.cursor.rowcount == 0:
                raise Exception(f'Error: rarity not found')

            self.cursor.execute('SELECT uuid FROM gacha WHERE uuid_rarity = %s and active = true',
                [rarity_uuid])

            records = self.cursor.fetchall()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return records 

    def getRarityBySymbol(self, symbol):
        try:
            self.cursor.execute('SELECT uuid from rarity where symbol = %s', 
                [symbol])

            if self.cursor.rowcount == 0:
                raise Exception(f'Error: rarity not found')
            
            record = self.cursor.fetchone()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return record

    def add(self, gacha_uuid, name, description, image_path, rarity_uuid):
        try:
            self.cursor.execute("""
                INSERT INTO gacha 
                    (uuid, name, description, image_path, uuid_rarity) 
                VALUES
                    (%s, %s, %s, %s, %s)""", 
            (gacha_uuid, name, description, image_path, rarity_uuid))

            self.cursor.execute("""
                SELECT g.uuid, g.name, description, image_path, r.name as rarity 
                FROM gacha g 
                    INNER JOIN rarity r on g.uuid_rarity = r.uuid WHERE g.uuid = %s""", 
                [gacha_uuid])

            if self.cursor.rowcount == 0:
                self.conn.rollback()
                raise Exception('Error: failed query')

            record = self.cursor.fetchone()

            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception('Error: failed query')

        return record

    def update(self, new_name, new_description, new_image_path, new_rarity_uuid, gacha_uuid):
        try:
            self.cursor.execute("""
                UPDATE gacha SET
                    name = COALESCE(%s, name),
                    description = COALESCE(%s, description),
                    image_path = COALESCE(%s, image_path),
                    uuid_rarity = COALESCE(%s, uuid_rarity)
                WHERE uuid = %s""", 
            [new_name, new_description, new_image_path, new_rarity_uuid, gacha_uuid])

            # update query returns the number of modified rows
            if self.cursor.rowcount == 0:
                self.conn.rollback()
                raise Exception(f'Error: failed update')

            self.cursor.execute("""
                SELECT g.uuid, g.name, description, image_path, r.name as rarity 
                FROM gacha g 
                    INNER JOIN rarity r on g.uuid_rarity = r.uuid WHERE g.uuid = %s""", 
                [gacha_uuid])

            if self.cursor.rowcount == 0:
                self.conn.rollback()
                raise Exception(f'Error: failed query')

            record = self.cursor.fetchone()

            self.conn.commit()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')
        
        return record

              
        