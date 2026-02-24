from kombu import Exchange, Queue

from PixivServer.config import rabbitmq

default_exchange = Exchange('pixivutil-exchange', type='direct', durable=True, delivery_mode=2)
dlx_exchange = Exchange('pixivutil-dlx', type='fanout', durable=True, delivery_mode=2)
dead_letter_queue = Queue(
    name="pixivutil-dead-letter",
    exchange=dlx_exchange,
    routing_key='',
    durable=True,
)

CELERY_QUEUES = (
    Queue(
        name="pixivutil-queue",
        exchange=default_exchange,
        routing_key='pixivutil-queue',
        durable=True,
        queue_arguments={
            'x-dead-letter-exchange': 'pixivutil-dlx',
            'x-max-priority': 3,
        },
    ),
)

BROKER_URL = rabbitmq.config.broker_url
CELERY_ACKS_LATE = True
CELERY_TASK_ACKS_LATE = True
CELERY_ACKS_ON_FAILURE_OR_TIMEOUT = False
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Keep broker-side queue priority behavior observable with a single worker.
# Without this, Celery can reserve multiple low-priority tasks before later high-priority tasks arrive.
CELERYD_PREFETCH_MULTIPLIER = 1
