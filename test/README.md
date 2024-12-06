-test close auction from admin:
  ```
curl -X PUT -k -H 'Content-Type: application/json' https://ase.localhost/admin/close/71520f05-80c5-4cb1-b05a-a9642f9aaaaa -b cookie.jar 
  ```
-test close own auction from user:
  ```
curl -X PUT -k -H 'Content-Type: application/json' https://ase.localhost/market/71520f05-80c5-4cb1-b05a-a9642f9aaaaa/close -b cookie.jar //auction with bids (test player)
curl -X PUT -k -H 'Content-Type: application/json' https://ase.localhost/market/71520f05-80c5-4cb1-b05a-a9642f9ccccc/close -b cookie.jar //auction without bids (test3 player)
  ```
-test payment:
//login as test 
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"username": "test", "password": "test"}' https://ase.localhost/login -c cookie.jar
  ```
//create auction
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"gacha_uuid": "09907f76-9b0f-4270-84a3-e9780b164ac4", "starting_price": 20}' -b cookie.jar https://ase.localhost/market
  ```
//login as test1
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"username": "test2", "password": "test"}' https://ase.localhost/login -c cookie.jar
  ```
//make bid as test1
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"offer": 400}' https://ase.localhost/market/ /bid -b cookie.jar
  ```
//login as test to see the currency update
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"username": "test", "password": "test"}' https://ase.localhost/login -c cookie.jar
  ```
//look at the currency
  ```
curl -X GET -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/user/currency -b cookie.jar
  ```

-test admin or user show_all auction:
//admin login
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"username": "admin", "password": "admin"}' https://ase.localhost/admin/login -c cookie.jar
  ```
//look all auction
  ```
curl -X GET -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/admin/market -b cookie.jar
  ```
//close an auction
  ```
curl -X PUT -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/admin/close/71520f05-80c5-4cb1-b05a-a9642f9ccccc -b cookie.jar
  ```
//look all auction
  ```
curl -X GET -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/admin/market -b cookie.jar
  ```
//user login
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"username": "test", "password": "test"}' https://ase.localhost/login -c cookie.jar
  ```
//look all auction
  ```
curl -X GET -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/market -b cookie.jar
  ```

-test admin or user show_one auction:

//user login
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"username": "test", "password": "test"}' https://ase.localhost/login -c cookie.jar
  ```
//look all auction
  ```
curl -X GET -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/market -b cookie.jar
  ```
//look the auction
  ```
curl -X GET -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/market/71520f05-80c5-4cb1-b05a-a9642f9ccccc -b cookie.jar
  ```
//admin login
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"username": "admin", "password": "admin"}' https://ase.localhost/admin/login -c cookie.jar
  ```
//look all auction
  ```
curl -X GET -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/admin/market -b cookie.jar
  ```
//look an auction
  ```
curl -X GET -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/admin/market/71520f05-80c5-4cb1-b05a-a9642f9ccccc -b cookie.jar
  ```
//close an auction
  ```
curl -X PUT -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/admin/close/71520f05-80c5-4cb1-b05a-a9642f9ccccc -b cookie.jar
  ```
//look the closed auction
  ```
curl -X GET -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/admin/market/71520f05-80c5-4cb1-b05a-a9642f9ccccc -b cookie.jar
  ```
//user login
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"username": "test", "password": "test"}' https://ase.localhost/login -c cookie.jar
  ```
//look the auction closed (not possible)
  ```
curl -X GET -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/market/71520f05-80c5-4cb1-b05a-a9642f9ccccc -b cookie.jar
  ```

-test admin can see transactions of a player
//admin login
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"username": "admin", "password": "admin"}' https://ase.localhost/admin/login -c cookie.jar
  ```
//list users player
  ```
curl -X GET -k -H 'Content-Type: application/json -H 'Accept: application/json' https://ase.localhost/admin/users -b cookie.jar
  ```
//look at the transactions of a single player
  ```
curl -X GET -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/admin/transaction/71520f05-80c5-4cb1-b05a-a9642f9ae44d -b cookie.jar
curl -X GET -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/admin/transaction/71520f05-80c5-4cb1-b05a-a9642f9ae111 -b cookie.jar
  ```

-test admin can see transactions by user_uuid and user can see own transacitons by user_uuid
//login as test 
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"username": "test", "password": "test"}' https://ase.localhost/login -c cookie.jar
  ```
//create auction
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"gacha_uuid": "09907f76-9b0f-4270-84a3-e9780b164ac4", "starting_price": 20}' -b cookie.jar https://ase.localhost/market
  ```
//login as test1
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"username": "test2", "password": "test"}' https://ase.localhost/login -c cookie.jar
  ```
//make bid as test1
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"offer": 400}' https://ase.localhost/market/ /bid -b cookie.jar
  ```
//admin login
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"username": "admin", "password": "admin"}' https://ase.localhost/admin/login -c cookie.jar
  ```
//admin look at the transactions of test2 (#TODO could be possible also to see of test??)
  ```
curl -X GET -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/admin/transaction/71520f05-80c5-4cb1-b05a-a9642f9ae111 -b cookie.jar
  ```
//test2 login
  ```
curl -X POST -k -H 'Content-Type: application/json' -d '{"username": "test2", "password": "test"}' https://ase.localhost/login -c cookie.jar
  ```
//test2 look at the own transactions
  ```
curl -X GET -k -H 'Content-Type: application/json' -H 'Accept: application/json' https://ase.localhost/user/transactions -b cookie.jar
```

### Running different Compose

```
docker compose -f "compose.develop.yaml" --env-file .test.env up
docker compose -f "compose.develop.yaml" --env-file .dev.env  down -v && docker compose -f "compose.develop.yaml" --env-file .dev.env up --build 
docker compose -f "compose.develop.yaml" --env-file .test.env  down -v && docker compose -f "compose.develop.yaml" --env-file .test.env up --build 
```
### Bandit

Lines skipped in bandit: 

- B311 - 11 lines skipped because randomness was not used for security purpose but just to create random username in locust and calculate rolls percentage
- B501 - 4 lines skipped because we are just using self signed certificates
- B105 - 1 lines skipped because we are not leaking any password but just calling a url that gives the password but hashed with salts
- B201 - 16 lines skipped because the factory methods with debug = True are only for testing and development purpose, indeed the production methods does not have it
- B104 - 24 lines skipped Binding the flask app in all interfaces ("0.0.0.0") it's safe in docker because container gives themself a level of isolation 

