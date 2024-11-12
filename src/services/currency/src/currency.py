from flask import Flask, request, jsonify, abort, render_template
import requests
import jwt

app = Flask(__name__)

SECRET = 'secret' # change secret for deployment

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({'response': "page not found"}), 404

@app.route('/', methods=['GET'])
def index():
    return render_template('buy.html')

@app.route('/currency/buy', methods=['POST'])
def buy():
    encoded_jwt = request.cookies.get('session')

    if not encoded_jwt:
        return jsonify({'response': 'You\'re not logged'})

    try:
        options = {
            'require': ['exp'], 
            'verify_signature': True, 
            'verify_exp': True
        }

        decoded_jwt = jwt.decode(encoded_jwt, SECRET, algorithms=['HS256'], options=options)
    except jwt.ExpiredSignatureError:
        return jsonify({'response': 'Expired token'})
    except jwt.InvalidTokenError:
        return jsonify({'response': 'Invalid token'})

    if 'uuid' not in decoded_jwt:
        return jsonify({'response': 'Try later'})

    player_uuid = decoded_jwt['uuid']
    purchase = request.json.get('purchase')

    player_purchasing = {
        'player_uuid' : player_uuid,
        'purchase' : purchase
    }

    r = requests.post(url='http://player_service:5000/currency/buy', json=player_purchasing)

    return r.text


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)




    
