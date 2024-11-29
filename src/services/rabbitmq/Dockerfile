FROM rabbitmq:3-management

RUN apt-get update && apt-get install -y curl

COPY ./10-defaults.conf /etc/rabbitmq/conf.d/