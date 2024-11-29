#!/usr/bin/bash

BASE_DIR="dbs"

if [ ! -d "$BASE_DIR" ]; then
    echo "Errore: la directory $BASE_DIR non esiste."
    exit 1
fi

for dir in "$BASE_DIR"/*; do
    if [ -d "$dir" ]; then
        echo "Entrando nella directory: $dir"
        
        cd "$dir" || { echo "Errore entrando in $dir"; exit 1; }

        if [ -f server.crt ] || [ -f server.key ]; then
            echo "Rimuovendo chiave e certificato esistenti in $dir..."
            rm -f server.crt server.key
        fi

        echo "Generando chiave e certificato per $dir..."
        openssl req -x509 -newkey rsa:4096 -nodes -out server.crt -keyout server.key -days 365 -subj "/CN=localhost"

        echo "Impostando i permessi..."
        sudo chown 999:999 server.crt
        sudo chown 999:999 server.key

        cd - > /dev/null
    fi
done

echo "Operazione completata."
