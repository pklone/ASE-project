from mycelery import app
import requests

@app.task
def add(x, y):
    return x + y

@app.task
def req():
    r = requests.get(url="https://gacha_service:5000/collection")
    return r.text , r.status_code

@app.task
def invoke_payment(auction_uuid):
    try:
        r = requests.post(url=f"https://market_service:5000/market/{auction_uuid}/payment")
    except Exception as e:
        return str(e)

    return r.text, r.status_code