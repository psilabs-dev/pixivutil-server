from celery import Celery
from celery.signals import setup_logging, worker_init, worker_shutdown
import logging

from PixivServer.config.rabbitmq import config as rabbitmq_config
from PixivServer.config.worker import config as worker_config
from PixivServer.service.pixiv import service as pixiv_service
from PixivServer.service.subscription import service as subscription_service

logger = logging.getLogger(__name__)

celery = Celery(__name__)
celery.conf.broker_url = rabbitmq_config.broker_url
celery.conf.result_backend = f"db+sqlite:///{worker_config.db}"

@worker_init.connect
def on_worker_init(*args, **kwargs):
    pixiv_service.open()
    subscription_service.open()
    return

@worker_shutdown.connect
def on_worker_shutdown(*args, **kwargs):
    pixiv_service.close()
    subscription_service.close()
    return

@setup_logging.connect
def config_loggers(*args, **kwargs):
    return

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(worker_config.subscription_time_seconds, run_artist_subscription_job.s(), name='Artist subscription job')
    sender.add_periodic_task(worker_config.subscription_time_seconds, run_tag_subscription_job.s(), name='Tag subscription job')

@celery.task(name='run_artist_subscription_job')
def run_artist_subscription_job():
    logger.info('Running scheduled member subscription job...')
    new_artworks_by_member_names = subscription_service.run_member_subscription_job()
    member_names = list(new_artworks_by_member_names.keys())
    if member_names:
        message = '[Scheduled job]: Downloaded new artworks from: ' + ', '.join(member_names)
    return True

@celery.task(name='run_tag_subscription_job')
def run_tag_subscription_job():
    '''
    Since this is calling process_tags directly cannot extract logs.
    '''
    logger.info('Running scheduled tag subscription job...')
    subscription_service.run_tag_subscription_job()

@celery.task(name="download_artworks_by_id")
def download_artworks_by_id(artwork_id: str):
    logger.info(f"Downloading artwork by ID: {artwork_id}.")
    artwork_name = pixiv_service.get_artwork_name(artwork_id)
    pixiv_service.download_artwork_by_id(artwork_id)
    return True

@celery.task(name="download_artworks_by_member_id")
def download_artworks_by_member_id(member_id: str):
    logger.info(f"Downloading artworks by member ID: {member_id}.")
    member_name = pixiv_service.get_member_name(member_id)
    pixiv_service.download_artworks_by_member_id(member_id)
    return True

@celery.task(name="download_artworks_by_tag")
def download_artworks_by_tag(tag: str):
    logger.info(f"Downloading artwork by tag: {tag}.")
    # TODO: verify the tag is retrieved.
    pixiv_service.download_artworks_by_tag(tag)
    return True
