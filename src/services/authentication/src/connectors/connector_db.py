import psycopg2
import psycopg2.extras

class AuthenticationConnectorDB:
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
    def getAdminByUsername(self, admin_username):
        try:
            self.cursor.execute('SELECT * FROM admin WHERE username = %s', 
                [admin_username])

            if self.cursor.rowcount == 0:
                raise ValueError(f'Error: admin not found')

            record = self.cursor.fetchone()
        except psycopg2.Error as e:
            raise Exception('Error: failed query')

        return record