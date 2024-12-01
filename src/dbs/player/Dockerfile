FROM cybertecpostgresql/postgresql-ee-demo:16

COPY ./init.sql /docker-entrypoint-initdb.d

COPY <<-'EOT' /usr/local/bin/ssl_init.sh
#!/bin/bash
# this script is run by root

set -e

DOCKER_SECRETS_PATH='/run/secrets'
POSTGRES_SSL_PATH='/var/lib/postgresql/ssl_files'
CERT_FILENAME='player_db.crt'
KEY_FILENAME='player_db.key'

if [ ! -d "${DOCKER_SECRETS_PATH}" ]; then
    echo "Error: ${DOCKER_SECRETS_PATH} directory not found"
    exit 1
elif [ ! -f "${DOCKER_SECRETS_PATH}/${CERT_FILENAME}" ] || [ ! -f "${DOCKER_SECRETS_PATH}/${KEY_FILENAME}" ]; then
    echo "Error: tls files not found"
    exit 1  
fi

# only run initialization on an empty data directory
if [ ! -d "${POSTGRES_SSL_PATH}" ]; then
    echo -n "Creating dir ${POSTGRES_SSL_PATH}... "
    mkdir "${POSTGRES_SSL_PATH}"
    echo 'Done!'

    echo -n 'Moving ssl files into postgres directory... '
    cp -t "${POSTGRES_SSL_PATH}" "${DOCKER_SECRETS_PATH}"/{"${CERT_FILENAME}","${KEY_FILENAME}"}
    mv "${POSTGRES_SSL_PATH}/${CERT_FILENAME}" "${POSTGRES_SSL_PATH}/server.crt"
    mv "${POSTGRES_SSL_PATH}/${KEY_FILENAME}" "${POSTGRES_SSL_PATH}/server.key"
    echo 'Done!'

    echo -n 'Setting permissions... '
    chown -R postgres:postgres "${POSTGRES_SSL_PATH}" && \
        chmod -R 700 "${POSTGRES_SSL_PATH}"
    echo -e 'Done!\n'
fi

exec "docker-entrypoint.sh" "$@"
EOT

RUN chmod u+x /usr/local/bin/ssl_init.sh

ENTRYPOINT ["ssl_init.sh"]

CMD ["-c", "ssl=on", "-c", "ssl_cert_file=/var/lib/postgresql/ssl_files/server.crt", "-c", "ssl_key_file=/var/lib/postgresql/ssl_files/server.key"]