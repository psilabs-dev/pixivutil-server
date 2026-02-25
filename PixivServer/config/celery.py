from kombu import Exchange, Queue

from PixivServer.config import rabbitmq

LEGACY_MAIN_EXCHANGE_NAME = "pixivutil-exchange"
LEGACY_MAIN_QUEUE_NAME = "pixivutil-queue"

MAIN_EXCHANGE_NAME = "pixivutil-v1-exchange"
DLX_EXCHANGE_NAME = "pixivutil-v1-dlx"
MAIN_QUEUE_NAME = "pixivutil-v1-queue"
MAIN_ROUTING_KEY = MAIN_QUEUE_NAME
DEAD_LETTER_QUEUE_NAME = "pixivutil-v1-dead-letter"
QUEUE_MAX_PRIORITY = 3

default_exchange = Exchange(MAIN_EXCHANGE_NAME, type='direct', durable=True, delivery_mode=2)
dlx_exchange = Exchange(DLX_EXCHANGE_NAME, type='fanout', durable=True, delivery_mode=2)
main_queue = Queue(
    name=MAIN_QUEUE_NAME,
    exchange=default_exchange,
    routing_key=MAIN_ROUTING_KEY,
    durable=True,
    queue_arguments={
        'x-dead-letter-exchange': DLX_EXCHANGE_NAME,
        'x-max-priority': QUEUE_MAX_PRIORITY,
    },
)
dead_letter_queue = Queue(
    name=DEAD_LETTER_QUEUE_NAME,
    exchange=dlx_exchange,
    routing_key='',
    durable=True,
)

CELERY_QUEUES = (main_queue,)

BROKER_URL = rabbitmq.config.broker_url
CELERY_ACKS_LATE = True
CELERY_TASK_ACKS_LATE = True
CELERY_ACKS_ON_FAILURE_OR_TIMEOUT = False
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Keep broker-side queue priority behavior observable with a single worker.
# Without this, Celery can reserve multiple low-priority tasks before later high-priority tasks arrive.
CELERYD_PREFETCH_MULTIPLIER = 1
