# ASE-project

## Getting started
Firstly, clone the repo.
```
git clone https://github.com/pklone/ASE-project.git
```
Then, go into the `src` directory. Now, build all the images.
```
docker compose build
```
Then, you can run the containers.
```
docker compose up -d
````
You can also do everything with one command.
```
docker compose up -d --build
```
The application is accessible from the proxy end-point at `https://ase.localhost`.

> [!IMPORTANT]
> End-point proxy uses a **self-signed** certificate to provide HTTPS. If you want to use `curl` to communicate with the APIs, use `-k` flag to disable CA signature verification.

## Testing
In order to test each service API without accessing the proxy, you can use another docker configuration file, i.e. `compose.testing.yaml`. It maps all the components (services, databases, etc.) with the external network, so you can access them from the host. Use the following command to run the application in _test mode_. 
```
docker compose -f compose.develop.yaml up -d --build
```

### Port mapping
Here is the list of all the accessible components and their related ports.
- Databases are mapped to ports in range `5432-5437`

  | Database                  | Port |
  | ------------------------- | ---- |
  | Player Database           | 5432 |
  | Admin Database            | 5433 |
  | Gacha Database            | 5434 |
  | Account Database          | 5435 |
  | Market Database           | 5436 |
  | Transaction Database      | 5437 |

- Services are mapped to ports in range `8080-8087`
  
  | Service                   | Port |
  | ------------------------- | ---- |
  | Player Service            | 8080 |
  | Authentication Service    | 8081 |
  | Collection Service        | 8082 |
  | Account Service           | 8083 |
  | Currency Service          | 8084 |
  | Admin Service             | 8085 |
  | Market Service            | 8086 |
  | Transaction Service       | 8087 |
  
- RabbitMQ is mapped to the ports `5672` and `15672`

### Database
You can connect to a database with the following command.
```
psql -U postgres
```
Here some useful `psql` commands.
```
\?                 # help
\l                 # list databases
\c <db>            # connect to a database
\conninfo          # show info about current database connetion
\dt                # list tables
\q                 # quit
```

### Curl
Here some useful `curl` commands to test the APIs. We provide also some [additional examples](/test/README.md).
- Register as a player, login, roll a new gacha and delete the account.
  ```
  curl -X POST -H 'Content-Type: application/json' -d '{"username": "kek", "password": "kek"}' -c cookie.jar http://127.0.0.1:8083/user
  curl -X POST -H 'Content-Type: application/json' -d '{"username": "kek", "password": "kek"}' -c cookie.jar http://127.0.0.1:8081/login
  curl -X GET -b cookie.jar http://127.0.0.1:8082/roll
  curl -X DELETE -b cookie.jar http://127.0.0.1:8083/user
  ```
- Register as a player, login, roll a gacha, get gachas uuids of own collection, create an auction, logout, login as `test` player, get the auctions uuids and make a bid.
  ```
  curl -X POST -H 'Content-Type: application/json' -d '{"username": "kek", "password": "kek"}' -c cookie.jar http://127.0.0.1:8083/user
  curl -X POST -H 'Content-Type: application/json' -d '{"username": "kek", "password": "kek"}' -c cookie.jar http://127.0.0.1:8081/login
  curl -X GET -b cookie.jar http://127.0.0.1:8082/roll
  curl -X GET -b cookie.jar http://127.0.0.1:8083/user/collection
  curl -X POST -H 'Content-Type: application/json' -d '{"gacha_uuid": "8930305e-262f-4ae9-92a0-f6d5dccc4d1f", "starting_price": 20}' -b cookie.jar http://127.0.0.1:8086/market
  curl -X DELETE -b cookie.jar http://127.0.0.1:8081/logout
  curl -X POST -H 'Content-Type: application/json' -d '{"username": "test", "password": "test"}' -c cookie.jar http://127.0.0.1:8081/login
  curl -X GET -H 'Accept: application/json' http://127.0.0.1:8086/market
  curl -X POST -H 'Content-Type: application/json' -d '{"offer": 50}' -b cookie.jar http://127.0.0.1:8086/market/6aa807c0-07c4-46ea-ae0a-ca027e7094d1/bid
  ```
- login as admin and insert a new gacha.
  ```
  curl -X POST -H 'Content-Type: application/json' -H 'Accept: application/json' -d '{"username": "admin", "password": "admin"}' -c cookie.jar http://127.0.0.1:8085/admin/login
  curl -X POST -b cookie.jar -F 'gacha_image=@/path/to/image' -F 'name=placeholder' -F 'description=placeholder' -F 'new_rarity=S' http://127.0.0.1:8085/admin/collection
  ```

### Compose Watch
It's possible to use `docker compose watch` to rebuild/resync the image/container when files change.
If you don't want to see container logs, use
```
docker compose up --build -d
docker compose watch --no-up
```
If instead you need to see them, use
```
docker compose up --build --watch
```

### Just
Here some useful `just` commands.
```
just           # show recipes as a list
just up        # docker compose up --build -d
just up w      # docker compose up -w
just up -      # docker compose up
just rs        # docker compose down && docker compose up --build -d
just rs v      # docker compose down -v && docker compose up --build -d
just rs b      # docker compose down && docker compose up --build
just rs d      # docker compose down && docker compose up -d
just rs w      # docker compose down && docker compose up -w
just rs v b    # docker compose down -v && docker compose up --build
just rs v d    # docker compose down -v && docker compose up -d
just rs v b w  # docker compose down -v && docker compose up --build -w
just rs -      # docker compose down && docker compose up
just w         # docker compose watch --no-up
just ps        # docker compose ps -a
just ps d      # docker ps -a
just run       # choose a just recipe to run
```
Note that `just up`, `just down` and `just exec` accept an **unlimited** number of args. In particular,
`just up` overwrites its default arguments, i.e.
```
just up                   # docker compose up --build -d
just up -d                # docker compose up -d
just up --watch           # docker compose up --watch
just up --build --watch   # docker compose up --build --watch
```
The recipe `just exec` will execute the following commands by default.
```
psql -U postgres    # if container is a db
/bin/bash           # if container is a service
```
As `just up`, you can overwrite these default commands. For example,
```
just exec /bin/bash
```
will run a shell no matter the container you choose

## Locust 
```
cd ASE-project/src
docker run --rm --network host -v "$PWD"/locust:/mnt/locust locustio/locust -f /mnt/locust/locustfile.py --host https://ase.localhost
```

## TODO
- ~~update `justfile` with `docker compose watch` and `docker compose down -v`~~
- use `<uuid:entity_uuid>` instead of `<string:entity_uuid>`
- use `with` statement to create db cursor instead of `try-catch`
- use single quotes instead of double quotes whenever is possible
- ~~store player's `uuid` instead of `id` inside jwt token~~
- ~~set gacha rarities percentages~~
- ~~use external volumes for db otherwise if db container crashes, we need to re-init it and we can lose data~~
- GUI
- ~~close auction in `market`~~
- ~~fix `show_one` and `show_all` functions in `market` (set gacha as dict instead of list)~~
- ~~transaction service~~
- https
- Oauth2
- ~~roll function~~
- ~~add `quantity` attribute in `player_gacha` table~~
- docker secrets 
- use foreign keys in `gacha_player` table (?)
- ~~fix `expired_at` in `market_db`~~
- ~~add decription in `gacha_db~~`
- check uuid with regex
- use `r.json` instead of `json.loads(r.text)`
- set timezone to UTC for `expire_at`
- set .gitignore to ignore only the `.env` file with `JUST_CHOOSER` variable
- ~~payment service~~
- postman tests
- ~~close auction when expire (by external service)~~
- ~~github actions~~
- set accessible/non-accessible routes on end-point gateway (security)
- ~~docker networks~~
- admin routes
- when a player makes a bid, checks if he has already the biggest bid (?)
- add link between `payment` and `player` services inside architecture image (and microfreshner)
- an admin can ban a player. Also, if a player wins an auction but he doesn't have enough money to pay the final price, 
  a counter will be increased by 1. When this counter becomes equal to 3, the player will be banned.
- use `pip install --no-cache-dir` to create smaller images
- remove id and use only uuid
- ~~jwt secret with env variable~~
- check `Accept` headers in all APIs
- ~~check if celery worker still close auction if it crashes (backend?)~~
- check consistency of functions that performs multi actions to other services or databases
- ~~market and transaction APIs in admin service~~
- add checks to market `close` API (e.g. admin can close every auction but player can close only his auctions)
- check null arguments in APIs
- ~~add delete gacha API~~
- ~~add message broker~~
- ~~check what service connects to `close` function in market (if caddy proxy connects to the functions, the player jwt must be checked)~~
- docker compose healthcheck
- delete id from database image
- change name of table `Player_Auction` to `Bid` in database image
- player can only see active auctions. Admin can see all
- ~~insert new gacha adding a new image~~
- http://ase.localhost must return an error (note: http instead of https)
- ~~delete account db since it is useless~~
- change `admin_db` to `authentication_db` 
- check caddyfile POST on gacha_service:5000/collection/ (only the admin can insert a new gacha)
- ~~merge pull request~~
- ~~`update` function in account.py~~
- make repo public
- cursor as dict in player registration
- unknown host when checking hostname
- ~~create a `test` directory and insert a README.md file with all the curl commands (there are too many curl commands in this README)~~
- add new password in modify_by_uuid inside `player.py`
- change `doc` in `docs`
- add http status codes to openAPI and to the python code
- change roll random technique (?)
- change deploy to limit docker container 
- add locust on docker compose for deploy
- fix roll workflow on locust