import logging

from celery import Celery
from celery.signals import setup_logging, worker_init, worker_shutdown

import PixivServer
import PixivServer.service
import PixivServer.service.pixiv
from PixivServer.config.celery import dead_letter_queue
from PixivServer.config.server import config as server_config

logger = logging.getLogger(__name__)

pixiv_worker = Celery(__name__)
pixiv_worker.config_from_object('PixivServer.config.celery')


@worker_init.connect
def on_worker_init(sender, **kwargs):
    with sender.app.connection() as conn:
        dead_letter_queue.bind(conn).declare()
    PixivServer.service.pixiv.service.open()


@worker_shutdown.connect
def on_worker_shutdown(*args, **kwargs):
    PixivServer.service.pixiv.service.close()
    return


@setup_logging.connect
def config_loggers(*args, **kwargs):
    return


# @celery.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     sender.add_periodic_task(worker_config.subscription_time_seconds, run_artist_subscription_job.s(), name='Artist subscription job')
#     sender.add_periodic_task(worker_config.subscription_time_seconds, run_tag_subscription_job.s(), name='Tag subscription job')

# @celery.task(name='run_artist_subscription_job')
# def run_artist_subscription_job():
#     logger.info('Running scheduled member subscription job...')
#     new_artworks_by_member_names = subscription_service.run_member_subscription_job()
#     member_names = list(new_artworks_by_member_names.keys())
#     if member_names:
#         message = '[Scheduled job]: Downloaded new artworks from: ' + ', '.join(member_names)
#     return True

# @celery.task(name='run_tag_subscription_job')
# def run_tag_subscription_job():
#     '''
#     Since this is calling process_tags directly cannot extract logs.
#     '''
#     logger.info('Running scheduled tag subscription job...')
#     subscription_service.run_tag_subscription_job()

# Register task modules, as @shared_task decorator only runs when the module is imported.
# until then, the task functions don't exist in Celery's registry.
import PixivServer.worker.download  # noqa: E402, F401
import PixivServer.worker.metadata  # noqa: E402, F401

if server_config.server_env == 'development':
    import PixivServer.worker.dev  # noqa: F401
