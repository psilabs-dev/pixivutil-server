from celery import Celery

from PixivServer.config.celery import DLX_EXCHANGE_NAME, MAIN_QUEUE_NAME, QUEUE_MAX_PRIORITY


def test_celery_failure_is_rejected_for_rabbitmq_dlq():
    app = Celery("pixivutil-test")
    app.config_from_object("PixivServer.config.celery")

    assert app.conf.task_acks_late is True
    assert app.conf.task_acks_on_failure_or_timeout is False


def test_main_queue_declares_dead_letter_exchange():
    app = Celery("pixivutil-test")
    app.config_from_object("PixivServer.config.celery")

    queues = {queue.name: queue for queue in app.conf.CELERY_QUEUES}
    assert MAIN_QUEUE_NAME in queues
    assert queues[MAIN_QUEUE_NAME].queue_arguments == {
        "x-dead-letter-exchange": DLX_EXCHANGE_NAME,
        "x-max-priority": QUEUE_MAX_PRIORITY,
    }


def test_worker_prefetch_multiplier_is_one_for_priority_fairness():
    app = Celery("pixivutil-test")
    app.config_from_object("PixivServer.config.celery")

    assert app.conf.worker_prefetch_multiplier == 1
