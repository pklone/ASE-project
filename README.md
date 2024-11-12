# ASE-project

## Database
You can connect to the database with the following command.
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

## Curl
Here some useful `curl` commands.
```
curl -X POST -H 'Content-Type: application/json' -d '{"username": "kek", "password": "kek"}' -c cookie.jar http://127.0.0.1:8083/user
curl -X POST -H 'Content-Type: application/json' -d '{"username": "kek", "password": "kek"}' -c cookie.jar http://127.0.0.1:8081/login
curl -X GET -b cookie.jar http://127.0.0.1:8082/roll
curl -X DELETE -b cookie.jar http://127.0.0.1:8083/user

curl -X POST -H 'Content-Type: application/json' -d '{"username": "test", "password": "test"}' -c cookie.jar http://127.0.0.1:8081/login
curl -X GET -b cookie.jar http://127.0.0.1:8083/user/collection
curl -X DELETE -b cookie.jar http://127.0.0.1:8081/logout
```

## Compose Watch
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

## Just
Here some useful `just` commands.
```
just         # show recipes as a list
just up      # docker compose up --build -d
just rs      # docker compose down && docker compose up --build -d
just rs v    # docker compose down -v && docker compose up --build -d
just w       # docker compose watch --no-up
just ps      # docker compose ps -a
just ps a    # docker ps -a
just run     # choose a just recipe to run
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

## TODO
- ~~update `justfile` with `docker compose watch` and `docker compose down -v`~~
- use `<uuid:entity_uuid>` instead of `<string:entity_uuid>`
- use `with` statement to create db cursor instead of `try-catch`
- use single quotes instead of double quotes whenever is possible
- ~~store player's `uuid` instead of `id` inside jwt token~~
- ~~set gacha rarities percentages~~
- use external volumes for db otherwise if db container crashes, we need to re-init it and we can lose data
- GUI
- market service
- transaction service
- payment service
- end-point gateway
- https
- Oauth2
- ~~roll function~~
- ~~add `quantity` attribute in `player_gacha` table~~
- docker secrets 
- use foreign keys in `gacha_player` table
- fix `expired_at` in `market_db` 
- add decription in `gacha_db`