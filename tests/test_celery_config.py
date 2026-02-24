from celery import Celery


def test_celery_failure_is_rejected_for_rabbitmq_dlq():
    app = Celery("pixivutil-test")
    app.config_from_object("PixivServer.config.celery")

    assert app.conf.task_acks_late is True
    assert app.conf.task_acks_on_failure_or_timeout is False


def test_main_queue_declares_dead_letter_exchange():
    app = Celery("pixivutil-test")
    app.config_from_object("PixivServer.config.celery")

    queues = {queue.name: queue for queue in app.conf.CELERY_QUEUES}
    assert "pixivutil-queue" in queues
    assert queues["pixivutil-queue"].queue_arguments == {
        "x-dead-letter-exchange": "pixivutil-dlx",
    }
