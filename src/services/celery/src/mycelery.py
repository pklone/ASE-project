from celery import Celery

broker_url = 'amqp://guest:guest@rabbitmq_broker:5672'

app = Celery('mycelery',
             broker=broker_url,
             backend='rpc://',
             include=['mytasks'])

# Optional configuration, see the application user guide.
#app.conf.update(
#    result_expires=3600,
#)

if __name__ == '__main__':
    app.start()