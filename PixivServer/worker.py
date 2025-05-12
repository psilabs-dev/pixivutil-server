import random
import time
from celery import Celery
from celery.signals import setup_logging, worker_init, worker_shutdown
import logging

import PixivServer
# from PixivServer.config.worker import config as worker_config
import PixivServer.service
import PixivServer.service.pixiv

logger = logging.getLogger(__name__)

pixiv_worker = Celery(__name__)
pixiv_worker.config_from_object('PixivServer.config.celery')

def __job_sleep():
    """
    Sleep a random interval between 1-5s for all jobs.
    Synchronous/blocking sleep.
    """
    time_to_sleep = random.uniform(1, 5)
    time.sleep(time_to_sleep)
    return 0

@worker_init.connect
def on_worker_init(*args, **kwargs):
    PixivServer.service.pixiv.service.open()
    return

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

@pixiv_worker.task(name="download_artworks_by_id", queue='pixivutil-queue')
def download_artworks_by_id(artwork_id: str):
    logger.info(f"Downloading artwork by ID: {artwork_id}.")
    # artwork_name = PixivServer.service.pixiv.service.get_artwork_name(artwork_id)
    PixivServer.service.pixiv.service.download_artwork_by_id(artwork_id)
    __job_sleep()
    return True

@pixiv_worker.task(name="download_artworks_by_member_id", queue='pixivutil-queue')
def download_artworks_by_member_id(member_id: str):
    logger.info(f"Downloading artworks by member ID: {member_id}.")
    # member_name = PixivServer.service.pixiv.service.get_member_name(member_id)
    PixivServer.service.pixiv.service.download_artworks_by_member_id(member_id)
    __job_sleep()
    return True

@pixiv_worker.task(name="download_artworks_by_tag", queue='pixivutil-queue')
def download_artworks_by_tag(tag: str, bookmark_count: int):
    logger.info(f"Downloading artwork by tag: {tag}. Bookmark minimum: {bookmark_count}")
    # TODO: verify the tag is retrieved.
    PixivServer.service.pixiv.service.download_artworks_by_tag(tag, bookmark_count)
    __job_sleep()
    return True
