from flask import Flask, request, jsonify
import psycopg2, os

app = Flask(__name__)

#set db connection

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")


@app.route('/database', methods=['POST','GET'])
def database():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        conn.close()
    except Exception as e:
        return str(e)

    return jsonify(db_version)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)