from mycelery import app
import requests

@app.task
def add(x, y):
    return x + y

@app.task
def req():
    r = requests.get(url="http://gacha_service:5000/collection")
    return r.text, r.status_code

@app.task
def invoke_payment(auction_uuid):
    try:
        r = requests.post(url=f"http://market_service:5000/market/{auction_uuid}/payment")
    except Exception as e:
        return jsonify({'response': str(e)}), 500

    return r.text, r.status_code