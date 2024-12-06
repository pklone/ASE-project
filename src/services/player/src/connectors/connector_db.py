import psycopg2
import psycopg2.extras

class PlayerConnectorDB:
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
            self.cursor.execute('SELECT id, uuid, username, password_hash, wallet from player')

            records = self.cursor.fetchall()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return records

    def getById(self, player_id):
        try:
            self.cursor.execute('SELECT id, uuid, username, wallet FROM player WHERE id = %s', 
                [player_id])

            if self.cursor.rowcount == 0:
                raise ValueError(f'Error: player not found')

            record = self.cursor.fetchone()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return record

    def getByUuid(self, player_uuid):
        try:
            self.cursor.execute('SELECT id, uuid, username, wallet, active FROM player WHERE uuid = %s', 
                [player_uuid])

            if self.cursor.rowcount == 0:
                raise ValueError(f'Error: player not found')

            record = self.cursor.fetchone()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return record

    def getWithPasswordHashByUsername(self, player_username):
        try:
            self.cursor.execute('SELECT id, uuid, username, password_hash, wallet, active FROM player WHERE username = %s', 
                [player_username])

            if self.cursor.rowcount == 0:
                raise ValueError(f'Error: player not found')

            record = self.cursor.fetchone()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return record

    def getByUsername(self, player_username):
        try:
            self.cursor.execute('SELECT id, uuid, username, wallet FROM player WHERE username = %s', 
                [player_username])

            if self.cursor.rowcount == 0:
                raise ValueError(f'Error: player not found')

            record = self.cursor.fetchone()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return record

    def add(self, player_uuid, username, password_hash):
        try:
            self.cursor.execute('SELECT 1 FROM player WHERE username = %s', 
                [username])

            if self.cursor.rowcount != 0:
                self.conn.rollback()
                raise ValueError('Error: player already created')

            self.cursor.execute('''
                INSERT INTO player 
                    (id, uuid, username, password_hash) 
                VALUES 
                    (DEFAULT, %s, %s, %s)''', 
            (player_uuid, username, password_hash))

            self.cursor.execute('SELECT id, uuid, username, wallet FROM player WHERE uuid = %s', 
                [player_uuid])

            if self.cursor.rowcount == 0:
                self.conn.rollback()
                raise Exception('Error: failed query')

            record = self.cursor.fetchone()

            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception('Error: failed query')

        return record

    def update(self, new_username, new_wallet, player_uuid):
        try:
            self.cursor.execute("""
                UPDATE player SET
                    username = COALESCE(%s, username),
                    wallet = COALESCE(%s, wallet)
                WHERE uuid = %s""", 
            (new_username, new_wallet, player_uuid))

            # update query returns the number of modified rows
            if self.cursor.rowcount == 0:
                self.conn.rollback()
                raise ValueError(f'Error: player not found')

            self.cursor.execute('SELECT id, uuid, username, wallet FROM player WHERE uuid = %s', 
                [player_uuid])

            if self.cursor.rowcount == 0:
                self.conn.rollback()
                raise Exception(f'Error: failed query')

            record = self.cursor.fetchone()

            self.conn.commit()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')
        
        return record

    def updateWallet(self, player_uuid, amount):
        try:
            self.cursor.execute('UPDATE player SET wallet = wallet + %s WHERE uuid = %s', 
                [amount, player_uuid])

            if self.cursor.rowcount == 0:
                self.conn.rollback()
                raise ValueError(f'Error: player not found')

            self.cursor.execute('SELECT id, uuid, username, wallet FROM player WHERE uuid = %s', 
                [player_uuid])

            if self.cursor.rowcount == 0:
                self.conn.rollback()
                raise Exception(f'Error: failed query')

            record = self.cursor.fetchone()

            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(f'Error: {str(e)}')

        return record


    def removeById(self, player_id):
        try:
            self.cursor.execute("SELECT 1 from player WHERE id = %s", 
                [player_id])
            
            if self.cursor.rowcount == 0:
                raise ValueError("Error: player not found")

            self.cursor.execute("DELETE FROM player WHERE id = %s", 
                [player_id])
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception('Error: failed query')

        return

    def removeByUuid(self, player_uuid, random_name):
        try:
            self.cursor.execute("SELECT 1 from player WHERE uuid = %s", 
                [player_uuid])
            
            if self.cursor.rowcount == 0:
                raise ValueError("Error: player not found")

            self.cursor.execute("UPDATE player SET active = false, wallet = 0, username = %s WHERE uuid = %s", 
                [random_name, player_uuid])
                
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception('Error: failed query')

        return

