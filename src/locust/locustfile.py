from locust import HttpUser, task, between
import logging
import json
import random
import string

def post_sign_up(workflow):
    payload = {  
        "username": workflow.random,
        "password": workflow.random  
    }
    try:
        response = workflow.client.post(
            "/user",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=False,
            catch_response=True  
        )   
    except Exception as e:
        logging.info(f"post_sign_up: error - {str(e)}")
    else:
        with response:
            if response.status_code != 201:
                if response.status_code == 400:
                    pass
                logging.info(f"post_sign_up: error - {response.text}")

def post_login(workflow):
    payload = {
        "username": workflow.random,
        "password": workflow.random
    }
    try:
        response = workflow.client.post(
            "/login",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=False,
            catch_response=True  
        )   
    except Exception as e:
        logging.info(f"post_login: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 400:
                    pass
                logging.info(f"post_login: error - {response.text}")
            else:
                workflow.is_logged_in = True
                workflow.is_logged_out = False

def get_user_collection(workflow):
    try:
        response = workflow.client.get(
            "/user/collection",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=False,
            catch_response=True  
        )   
    except Exception as e:
        logging.info(f"get_user_collection: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 400:
                    pass
                logging.info(f"get_user_collection: error - {response.text}")

def delete_logout(workflow):
    try:
        response = workflow.client.delete(
            "/logout",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=False,
            catch_response=True 
        )   
    except Exception as e:
        logging.info(f"delete_logout: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 400:
                    pass
                logging.info(f"delete_logout: error - {response.text}")
            else:
                workflow.is_logged_in = False
                workflow.is_logged_out = True

def post_buy_currency(workflow):
    payload = {
        "purchase": 10000
    }
    try:
        response = workflow.client.post(
            "/currency/buy",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=False,
            catch_response=True  
        )   
    except Exception as e:
        logging.info(f"post_buy_currency: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 400:
                    pass
                logging.info(f"post_buy_currency: error - {response.text}")

def get_currency(workflow):
    try:
        response = workflow.client.get(
            "/user/currency",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=False,
            catch_response=True  
        )   
    except Exception as e:
        logging.info(f"get_currency: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 400:
                    pass
                logging.info(f"get_currency: error - {response.text}")
            else:
                workflow.currency = response.json()["response"]

def get_roll(workflow):
    try:
        response = workflow.client.get(
            "/roll",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=False,
            catch_response=True  
        )   
    except Exception as e:
        logging.info(f"get_roll: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 400:
                    pass
                logging.info(f"get_roll: error - {response.text}")
            else:
                #workflow.gacha_uuid = response.json()["response"]["uuid"]
                #logging.info(f"get_roll: ok!")
                #if response.json().get("response") and response.json()["response"].get("uuid"):
                #    workflow.gacha_uuid = response.json()["response"]["uuid"] #TODO: check getAllRarity query into connector.py
                #else:
                #    logging.info(f"get_roll: no gacha_uuid")
                gacha_uuid = response.json()["response"]["uuid"]
                return gacha_uuid
            
def post_create_auction(workflow, gacha_uuid):
    payload = {
        "gacha_uuid": gacha_uuid,
        "starting_price": 100
    }
    try:
        response = workflow.client.post(
            "/market",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=False,
            catch_response=True  
        )   
    except Exception as e:
        logging.info(f"post_create_auction: error - {str(e)}")
    else:
        with response:
            if response.status_code != 201:
                if response.status_code == 500:
                    logging.info(f"post_create_auction: error - {response.text}")
                else:
                    pass
            else:
                 pass

def get_auction(workflow):
    try:
        response = workflow.client.get(
            "/market",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=False,
            catch_response=True  
        )   
    except Exception as e:
        logging.info(f"get_auction: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 400:
                    pass
                logging.info(f"get_auction: error - {response.text}")
            else:
                auction = response.json()["response"]
                return auction

def get_auction_by_uuid(workflow, auction_uuid):
    try:
        response = workflow.client.get(
            f"/market/{auction_uuid}",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=False,
            catch_response=True  
        )   
    except Exception as e:
        logging.info(f"get_auction_by_uuid: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 400:
                    pass
                logging.info(f"get_auction_by_uuid: error - {response.text}")
            else:
                auction = response.json()["response"]
                return auction
            
def post_bid(workflow, auction_uuid, offer):
    payload = {
        "offer": offer
    }
    try:
        response = workflow.client.post(
            f"/market/{auction_uuid}/bid",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=False,
            catch_response=True
        )
    except Exception as e:
        logging.info(f"post_bid: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 400:
                    pass
                logging.info(f"post_bid: error - {response.text}")
            else:
                logging.info(f"post_bid: Successfully placed bid on auction {auction_uuid}")


class UserCollectionWorkflow(HttpUser):

    wait_time = between(1, 5)

    def on_start(self):
        self.is_logged_in = False
        self.is_logged_out = True
        self.random = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        post_sign_up(self)
        post_login(self)

    @task(3)
    def user_collection(self):
        if self.is_logged_in:
            get_user_collection(self)
        else:
            pass
    
    @task(1)
    def logout(self):
        if self.is_logged_in:
            delete_logout(self)
        else:
            pass

class UserGachaWorkflow(HttpUser):

    wait_time = between(1, 5)

    def on_start(self):
        self.is_logged_in = False
        self.is_logged_out = True
        self.currency = 0
        self.random = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        post_sign_up(self)
        post_login(self)
        post_buy_currency(self)
        get_currency(self)

    @task(1)
    def create_auction(self):
        if self.is_logged_in and self.currency >= 10:
            gacha_uuid = get_roll(self)
            if gacha_uuid:
                post_create_auction(self, gacha_uuid)
        else:
            pass
    
    def on_end(self):
        if self.is_logged_in:
            delete_logout(self)
        else:
            pass
    
class UserMarketWorkflow(HttpUser):

    wait_time = between(1, 5)

    def on_start(self):
        self.is_logged_in = False
        self.is_logged_out = True
        self.random = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        post_sign_up(self)
        post_login(self)
    
    @task(1)
    def bid(self):
        if self.is_logged_in:
            auctions = get_auction(self)
            if not auctions:
                logging.info("No auctions available to bid on.")
                pass

            non_owned_auctions = [
                auction for auction in auctions
                if auction["player_username"] != self.random
            ]

            if not non_owned_auctions:
                logging.info("No auctions available to bid on.")
                pass

            chose_auction = random.choice(non_owned_auctions)
            auction_uuid = chose_auction["auction_uuid"]
            target_auction = get_auction_by_uuid(self, auction_uuid)
            if target_auction["base_price"] >= target_auction["actual_offer"]:
                offer = target_auction["base_price"] + random.randint(1, 100)
            else:
                offer = target_auction["actual_offer"] + random.randint(1, 100)
            post_bid(self, auction_uuid, offer)
        else:
            logging.info("User not logged in.")
            pass