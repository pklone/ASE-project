from celery import Celery
import os
import ssl

CERT_PATH= os.getenv("CERT_PATH")
KEY_PATH= os.getenv("KEY_PATH")

broker_url = 'amqps://rabbitmq_broker:5671'

app = Celery('mycelery',
             broker=broker_url,
             backend='rpc://',
             include=['mytasks'])

app.conf.broker_use_ssl = {
    'keyfile': KEY_PATH,
    'certfile': CERT_PATH,
    'cert_reqs': ssl.CERT_NONE
}


# Optional configuration, see the application user guide.
#app.conf.update(
#    result_expires=3600,
#)

if __name__ == '__main__':
    app.start()