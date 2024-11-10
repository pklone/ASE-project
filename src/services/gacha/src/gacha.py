from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__, static_url_path='/assets')

#set db connection
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({'response': "page not found"}), 404

@app.route('/collection', methods=['GET'])
def show_all():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor()
        cursor.execute("SELECT g.id, uuid, g.name, description, image_path, r.name as rarity FROM gacha g INNER JOIN rarity r on g.rarity_id = r.id")
        records = cursor.fetchall()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return str(e)

    return jsonify(records)

@app.route('/collection/<string:gacha_uuid>', methods=['GET'])
def show(gacha_uuid):
    result = {}

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM gacha WHERE uuid = %s", [gacha_uuid])
        record = cursor.fetchone()

        if record:
            result = record

        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return str(e)

    return jsonify(result)

@app.route('/collection/user/<int:player_id>', methods=['GET'])
def show_by_player(player_id):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT g.id, uuid, g.name, description, image_path, r.name as rarity 
            FROM gacha g 
                INNER JOIN rarity r on g.id_rarity = r.id 
                INNER JOIN player_gacha pg on g.id = pg.id_gacha 
            WHERE pg.id_player = %s""", 
        [player_id])
        records = cursor.fetchall()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        return str(e)

    return jsonify(records)

@app.route('/roll', methods=['GET'])
def roll():
    pass

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)