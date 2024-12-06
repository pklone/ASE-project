from locust import HttpUser, task, between
import logging
import json
import threading
import random as rd
import string
import warnings
from urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter('ignore', InsecureRequestWarning)

lock = threading.Lock()
rarity_counter = {
    "Common": 0,
    "Uncommon": 0,
    "Rare": 0,
    "Epic": 0,
    "Legendary": 0
}

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
                if response.status_code == 500:
                    logging.info(f"post_sign_up: error - {response.text}")
                else:
                    logging.info(f"post_sign_up: error - {response.text}")
                    response.success()

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
                if response.status_code == 500:
                    logging.info(f"post_login: error - {response.text}")
                else:
                    logging.info(f"post_login: error - {response.text}")
                    response.success()
            else:
                workflow.is_logged_in = True
                workflow.is_logged_out = False
                return response.headers
            
def post_admin_login(workflow):
    payload = {
        "username": "admin",
        "password": "admin"
    }
    try:
        response = workflow.client.post(
            "/admin/login",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=False,
            catch_response=True
        )
    except Exception as e:
        logging.info(f"post_admin_login: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 500:
                    logging.info(f"post_admin_login: error - {response.text}")
                else:
                    logging.info(f"post_admin_login: error - {response.text}")                    
                    response.success()
            else:
                workflow.admin_logged_in = True
                workflow.admin_logged_out = False
                return response.headers
            
def get_admin_users(workflow):
    try:
        response = workflow.client.get(
            "/admin/users",
            headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": workflow.admin_headers["Authorization"]},
            verify=False,
            catch_response=True
        )
    except Exception as e:
        logging.info(f"get_admin_users: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 500:
                    logging.info(f"get_admin_users: error - {response.text}")
                else:
                    logging.info(f"get_admin_users: error - {response.text}")
                    response.success()
            else:
                users = response.json()["response"]
                return users

def get_admin_user_collection(workflow, user_uuid):
    try:
        response = workflow.client.get(
            f"/admin/users/{user_uuid}",
            headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": workflow.admin_headers["Authorization"]},
            verify=False,
            catch_response=True
        )
    except Exception as e:
        logging.info(f"get_user_collection: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 500:
                    logging.info(f"get_user_collection: error - {response.text}")
                else:
                    logging.info(f"get_user_collection: error - {response.text}")
                    response.success()
            else:
                user_collection = response.json()["response"]
                return user_collection
            
def post_admin_payment(workflow, auction_uuid):
    try:
        response = workflow.client.post(
            f"/admin/payment/{auction_uuid}",
            headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": workflow.admin_headers["Authorization"]},
            verify=False,
            catch_response=True
        )
    except Exception as e:
        logging.info(f"post_admin_payment: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 500:
                    logging.info(f"post_admin_payment: error - {response.text}")
                else:
                    logging.info(f"post_admin_payment: error - {response.text}")
                    response.success()

def get_admin_auction(workflow):
    try:
        response = workflow.client.get(
            "/admin/market",
            headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": workflow.admin_headers["Authorization"]},
            verify=False,
            catch_response=True
        )
    except Exception as e:
        logging.info(f"get_admin_auction: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 500:
                    logging.info(f"get_admin_auction: error - {response.text}")
                else:
                    logging.info(f"get_admin_auction: error - {response.text}")
                    response.success()
            else:
                auctions = response.json()["response"]
                return auctions

def get_user_transactions(workflow):
    try:
        response = workflow.client.get(
            f"/user/transactions",
            headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": workflow.headers["Authorization"]},
            verify=False,
            catch_response=True
        )
    except Exception as e:
        logging.info(f"get_user_transactions: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 500:
                    logging.info(f"get_user_transactions: error - {response.text}")
                else:
                    logging.info(f"get_user_transactions: error - {response.text}")
                    response.success()
            else:
                transactions = response.json()["response"]
                return transactions

def get_user_collection(workflow):
    try:
        response = workflow.client.get(
            "/user/collection",
            headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": workflow.headers["Authorization"]},
            verify=False,
            catch_response=True  
        )   
    except Exception as e:
        logging.info(f"get_user_collection: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 500:
                    logging.info(f"get_user_collection: error - {response.text}")
                else:
                    logging.info(f"get_user_collection: error - {response.text}")
                    response.success()

def delete_logout(workflow):
    try:
        response = workflow.client.delete(
            "/logout",
            headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": workflow.headers["Authorization"]},
            verify=False,
            catch_response=True 
        )   
    except Exception as e:
        logging.info(f"delete_logout: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 500:
                    logging.info(f"delete_logout: error - {response.text}")
                else:
                    logging.info(f"delete_logout: error - {response.text}")
                    response.success()
            else:
                workflow.is_logged_in = False
                workflow.is_logged_out = True

def post_buy_currency(workflow):
    payload = {
        "purchase": 10000
    }
    try:
        response = workflow.client.put(
            "/currency/buy",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": workflow.headers["Authorization"]},
            verify=False,
            catch_response=True  
        )   
    except Exception as e:
        logging.info(f"post_buy_currency: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 500:
                    logging.info(f"post_buy_currency: error - {response.text}")
                else:
                    logging.info(f"post_buy_currency: error - {response.text}")
                    response.success()

def get_currency(workflow):
    try:
        response = workflow.client.get(
            "/user/currency",
            headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": workflow.headers["Authorization"]},
            verify=False,
            catch_response=True
        )   

    except Exception as e:
        logging.info(f"get_currency: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 500:
                    logging.info(f"get_currency: error - {response.text}")
                else:
                    logging.info(f"get_currency: error - {response.text}")
                    response.success()
            else:
                return response.json()["response"]
            
def get_roll(workflow):
    try:
        response = workflow.client.get(
            "/roll",
            headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": workflow.headers["Authorization"]},
            verify=False,
            catch_response=True  
        )   
    except Exception as e:
        logging.info(f"get_roll: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 500:
                    logging.info(f"get_roll: error - {response.text}")
                else:
                    logging.info(f"get_roll: error - {response.text}")
                    response.success()
            else:
                gacha_uuid = response.json()["response"]["uuid"]
                gacha_rarity = response.json()["response"]["rarity"]
                return [gacha_uuid, gacha_rarity]
            
def post_create_auction(workflow, gacha_uuid):
    payload = {
        "gacha_uuid": gacha_uuid,
        "starting_price": 100
    }
    try:
        response = workflow.client.post(
            "/market",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": workflow.headers["Authorization"]},
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
                    logging.info(f"post_create_auction: error - {response.text}")
                    response.success()

def get_auction(workflow):
    try:
        response = workflow.client.get(
            "/market",
            headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": workflow.headers["Authorization"]},
            verify=False,
            catch_response=True  
        )   
    except Exception as e:
        logging.info(f"get_auction: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 500:
                    logging.info(f"get_auction: error - {response.text}")
                else:
                    logging.info(f"get_auction: error - {response.text}")
                    response.success()
            else:
                auction = response.json()["response"]
                return auction

def get_auction_by_uuid(workflow, auction_uuid):
    try:
        response = workflow.client.get(
            f"/market/{auction_uuid}",
            headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": workflow.headers["Authorization"]},
            verify=False,
            catch_response=True  
        )   
    except Exception as e:
        logging.info(f"get_auction_by_uuid: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 500:
                    logging.info(f"get_auction_by_uuid: error - {response.text}")
                else:
                    logging.info(f"get_auction_by_uuid: error - {response.text}")
                    response.success()
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
            headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": workflow.headers["Authorization"]}, 
            verify=False,
            catch_response=True
        )
    except Exception as e:
        logging.info(f"post_bid: error - {str(e)}")
    else:
        with response:
            if response.status_code != 200:
                if response.status_code == 500:
                    logging.info(f"post_bid: error - {response.text}")
                else:
                    logging.info(f"post_bid: error - {response.text}")
                    response.success()

def print_rarity():
    logging.info(f"Common: {rarity_counter['Common']}%, Uncommon: {rarity_counter['Uncommon']}%, Rare: {rarity_counter['Rare']}%, Epic: {rarity_counter['Epic']}%, Legendary: {rarity_counter['Legendary']}%")


class UserCollectionWorkflow(HttpUser):

    host = "https://localhost"
    wait_time = between(1, 5)

    def on_start(self):
        self.is_logged_in = False
        self.is_logged_out = True
        self.random = ''.join(rd.choices(string.ascii_lowercase + string.digits, k=8)) # nosec B311 Randomness is not used for security purposes
        post_sign_up(self)
        self.headers = post_login(self)

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

    host = "https://localhost"
    wait_time = between(1, 5)

    def on_start(self):
        self.is_logged_in = False
        self.is_logged_out = True
        self.currency = 0
        self.random = ''.join(rd.choices(string.ascii_lowercase + string.digits, k=8)) # nosec B311 Randomness is not used for security purposes
        post_sign_up(self)
        self.headers = post_login(self)
        post_buy_currency(self)
        self.currency = get_currency(self)

    @task(2)
    def create_auction(self):
        if self.is_logged_in and self.currency >= 10:
            gacha_uuid = get_roll(self)[0]
            if gacha_uuid:
                post_create_auction(self, gacha_uuid)
        else:
            pass
    
    def on_stop(self):
        if self.is_logged_in:
            delete_logout(self)
    
class UserMarketWorkflow(HttpUser):

    host = "https://localhost"
    wait_time = between(1, 5)

    def on_start(self):
        self.is_logged_in = False
        self.is_logged_out = True
        self.random = ''.join(rd.choices(string.ascii_lowercase + string.digits, k=8)) # nosec B311 Randomness is not used for security purposes
        post_sign_up(self)
        self.headers = post_login(self)
    
    @task(3)
    def bid(self):
        if self.is_logged_in:
            non_owned_auctions = []
            auctions = get_auction(self)
            if not auctions:
                logging.info("No auctions available to bid on.")
                return

            for auction in auctions:
                if auction:
                    if auction.get("Player"):
                        if auction["Player"]["username"]!= self.random: # nosec B311 Randomness is not used for security purposes
                            non_owned_auctions.append(auction)

            if non_owned_auctions:
                chose_auction = rd.choice(non_owned_auctions) # nosec B311 Randomness is not used for security purposes
                auction_uuid = chose_auction["auction_uuid"]
                target_auction = get_auction_by_uuid(self, auction_uuid)
                if target_auction["base_price"] >= target_auction["actual_offer"]:
                    offer = target_auction["base_price"] + rd.randint(1, 100) # nosec B311 Randomness is not used for security purposes
                else:
                    offer = target_auction["actual_offer"] + rd.randint(1, 100) # nosec B311 Randomness is not used for security purposes
                post_bid(self, auction_uuid, offer)
            else:
                logging.info("No auctions available to bid on.")
        else:
            logging.info("User not logged in.")
    
    @task(3)
    def transaction(self):
        if self.is_logged_in:
            transactions = get_user_transactions(self)

    def on_stop(self):
        if self.is_logged_in:
            delete_logout(self)

class RarityCounterWorkflow(HttpUser): 

    host = "https://localhost"
    wait_time = between(1, 5)        

    def on_start(self):
        self.is_logged_in = False
        self.is_logged_out = True
        self.random = ''.join(rd.choices(string.ascii_lowercase + string.digits, k=8)) # nosec B311 Randomness is not used for security purposes
        post_sign_up(self)
        self.headers = post_login(self)
        post_buy_currency(self)

    @task(3)
    def rarity_counter(self):
        if self.is_logged_in:
            rarity = get_roll(self)
            if rarity:
                with lock:
                    rarity_counter[rarity[1]] += 1     
    
    def on_stop(self):
        total = sum(rarity_counter.values())
        for key in rarity_counter:
            rarity_counter[key] = int(rarity_counter[key] * 100 / total)
        print_rarity()
        if self.is_logged_in:
            delete_logout(self)

class AdminWorkflow(HttpUser):

    host = "https://localhost:8443"
    wait_time = between(1, 5)

    def on_start(self):
        self.admin_logged_in = False
        self.admin_logged_out = True
        self.admin_headers = post_admin_login(self)
    
    @task(3)
    def admin_users(self):
        if self.admin_logged_in:
            users = get_admin_users(self)
            if users:
                user = rd.choice(users) # nosec B311 Randomness is not used for security purposes
                user_uuid = user['uuid']
                user_collection = get_admin_user_collection(self, user_uuid)

    @task(1)
    def admin_payment(self):
        if self.admin_logged_in:
            auctions = get_admin_auction(self)

    task(1)
    def admin_logout(self):
        if self.admin_logged_in:
            delete_logout(self)