from mycelery import app
import requests
import pybreaker

circuitbreaker = pybreaker.CircuitBreaker(
            fail_max=5, 
            reset_timeout=60*5
        )

@app.task
def add(x, y):
    return x + y

@app.task
def req():
    r = circuitbreaker.call(requests.get, "https://gacha_service:5000/collection", verify=False) # nosec B501 We are using self signed certificates
    return r.text , r.status_code

@app.task
def invoke_payment(auction_uuid):
    try:
        r = circuitbreaker.call(requests.post, f"https://market_service:5000/market/{auction_uuid}/payment", verify=False) # nosec B501 We are using self signed certificates
    except Exception as e:
        return str(e)

    return r.text, r.status_code