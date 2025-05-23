from kombu import Exchange, Queue

from PixivServer.config import rabbitmq

default_exchange = Exchange('pixivutil-exchange', type='direct', durable=True, delivery_mode=2)

CELERY_QUEUES = (
    Queue(name="pixivutil-queue", exchange=default_exchange, routing_key='pixivutil-queue', durable=True),
)

BROKER_URL = rabbitmq.config.broker_url
CELERY_ACKS_LATE = True
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
