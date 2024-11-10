from flask import Flask, request, jsonify, abort
import requests

app = Flask(__name__)

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({'response': "page not found"}), 404

@app.route('/currency/buy', methods=['POST'])
def buy():
    cookie = request.json['cookie']

    # extract player uuid from cookie (to redefine)
    player_uuid = cookie
    purchase = request.json['purchase']

    player_purchasing = {
        'player_uuid' : player_uuid,
        'purchase' : purchase
    }

    r = requests.post(url='http://player_service:5000/currency', json=player_purchasing)

    return r.text


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)




    
