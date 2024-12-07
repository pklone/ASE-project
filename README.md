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
The application is accessible from the following endpoints.
```
https://localhost       # client end-point
https://localhost:8443  # admin end-point
```

> [!IMPORTANT]
> End-point proxy uses a **self-signed** certificate to provide HTTPS. If you want to use `curl` to communicate with the APIs, use `-k` flag to disable CA signature verification.

## Testing
In order to test each service API without accessing the proxy, you can use another docker configuration file, i.e. `compose.develop.yaml`. It allows to perform both _unit test_ and _integration tests_. It also maps all the components (services, databases, etc.) with the external network, so you can access them from the host. Use the following commands to test the application.
```
docker compose -f compose.develop.yaml --env-file .test.env  up -d --build   # unit tests
docker compose -f compose.develop.yaml --env-file .dev.env up -d --build   # integration tests
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

- Services are mapped to ports in range `8080-8088`
  
  | Service                   | Port |
  | ------------------------- | ---- |
  | Player Service            | 8080 |
  | Authentication Service    | 8081 |
  | Collection Service        | 8082 |
  | Account Service           | 8083 |
  | Currency Service          | 8088 |
  | Admin Service             | 8085 |
  | Market Service            | 8086 |
  | Transaction Service       | 8087 |
  
- RabbitMQ is mapped to the ports `5672` and `15672`

## Locust
You can run performance tests using `locust`. Enter `src` directory and run the following command to start a locust container.
```
docker run --rm --network host -v "$PWD"/locust:/mnt/locust locustio/locust -f /mnt/locust/locustfile.py --headless -u 100 -r 5 --run-time 120 --stop-timeout 10s
```
At the end of the execution, locust will print a summary of the rarities probability distribution.

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
- Register as a player, login, purchase currency and roll a new gacha.
  ```
  curl -X POST -H 'Content-Type: application/json' -d '{"username": "testing123", "password": "testing123"}' -k https://127.0.0.1:8083/user
  curl -X POST -s -o /dev/null -w 'Authorization: %header{Authorization}' -H 'Content-Type: application/json' -d '{"username": "testing123", "password": "testing123"}' -k https://127.0.0.1:8081/login > headers.txt
  curl -X PUT -H @headers.txt -H 'Content-Type: application/json' -d '{"purchase": 100}' -k https://127.0.0.1:8088/currency/buy 
  curl -X GET -H @headers.txt -H 'Accept: application/json' -k https://127.0.0.1:8082/roll
  ```
- Register as a player, login, roll a gacha, create an auction, logout, login as `test` player, get the auctions uuids and make a bid.
  ```
  curl -X POST -H 'Content-Type: application/json' -d '{"username": "testing123", "password": "testing123"}' -k https://127.0.0.1:8083/user
  curl -X POST -s -o /dev/null -w 'Authorization: %header{Authorization}' -H 'Content-Type: application/json' -d '{"username": "testing123", "password": "testing123"}' -k https://127.0.0.1:8081/login > headers.txt
  curl -X PUT -H @headers.txt -H 'Content-Type: application/json' -d '{"purchase": 100}' -k https://127.0.0.1:8088/currency/buy
  curl -X POST -H @headers.txt -H 'Content-Type: application/json' -H 'Accept: application/json' -d '{"gacha_uuid": "<gacha_uuid>", "starting_price": 20}' -k https://127.0.0.1:8086/market
  curl -X DELETE -H @headers.txt -k https://127.0.0.1:8081/logout
  curl -X POST -H 'Content-Type: application/json' -d '{"username": "testing345", "password": "testing345"}' -k https://127.0.0.1:8083/user
  curl -X POST -s -o /dev/null -w 'Authorization: %header{Authorization}' -H 'Content-Type: application/json' -d '{"username": "testing345", "password": "testing345"}' -k https://127.0.0.1:8081/login > headers.txt
  curl -X GET -H @headers.txt -H 'Accept: application/json' -k https://127.0.0.1:8086/market
  curl -X POST -H @headers.txt -H 'Content-Type: application/json' -d '{"offer": 350}' -k https://127.0.0.1:8086/market/<auction_uuid>/bid
  ```
- login as admin and insert a new gacha.
  ```
  curl -X POST -s -o /dev/null -w 'Authorization: %header{Authorization}' -H 'Content-Type: application/json' -d '{"username": "admin123", "password": "admin123"}' -k https://127.0.0.1:8085/admin/login > headers.txt
  curl -X POST -F 'gacha_image=@/path/to/image' -F 'name=placeholder' -F 'description=placeholder' -F 'rarity=S' -k https://127.0.0.1:8082/admin/collection
  ```


### Compose Watch
It's possible to use `docker compose watch` to rebuild/resync the image/container when files change.
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
just logs      # choose a container and run docker compose logs
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