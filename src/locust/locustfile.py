from locust import HttpUser, task, between
import json
import random
import string

class UserWorkflow(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        self.random = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.sign_up()
        self.post_login()
        
    def sign_up(self):
        payload = {  
            "username": self.random,
            "password": self.random  
        }
        
        with self.client.post(
            "/user",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=False,
            catch_response=True  
        ) as response:
            if response.status_code == 201:
                pass
            else:
                response.failure(f"Request failed with status code {response.status_code}")


    def post_login(self):
        payload = {
            "username": self.random,
            "password": self.random
        }

        with self.client.post(
            "/login",  
            data=json.dumps(payload),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=False,
            catch_response=True  
        ) as response:
            if response.status_code == 200:
                pass
            else:
                response.failure(f"Login failed with status code {response.status_code}")

    @task(1)
    def get_user_collection(self):
        with self.client.get(
            "/user/collection",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=False,
            catch_response=True 
        ) as response:
            if response.status_code == 200:
                pass
            else:
                response.failure(f"Failed to retrieve collection with status code {response.status_code}")

