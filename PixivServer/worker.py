import random
import time
import traceback
from celery import Celery
from celery.signals import setup_logging, worker_init, worker_shutdown
import logging

import PixivServer
# from PixivServer.config.worker import config as worker_config
import PixivServer.service
import PixivServer.service.pixiv
from PixivServer.models.pixiv_worker import (
    DeleteArtworkByIdRequest,
    DownloadArtworkByIdRequest,
    DownloadArtworksByMemberIdRequest,
    DownloadArtworksByTagsRequest,
    DownloadArtworkMetadataByIdRequest,
    DownloadMemberMetadataByIdRequest,
    DownloadSeriesMetadataByIdRequest,
    DownloadTagMetadataByIdRequest,
)

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
def download_artworks_by_id(request_dict: dict):
    try:
        request = DownloadArtworkByIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log("info", f"Downloading artwork by ID: {request.artwork_id}.")
        PixivServer.service.pixiv.service.download_artwork_by_id(request)
        return True
    except Exception as e:
        logger.error(f"Error in download_artworks_by_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        __job_sleep()

@pixiv_worker.task(name="download_artworks_by_member_id", queue='pixivutil-queue')
def download_artworks_by_member_id(request_dict: dict):
    try:
        request = DownloadArtworksByMemberIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log("info", f"Downloading artworks by member ID: {request.member_id}.")
        PixivServer.service.pixiv.service.download_artworks_by_member_id(request)
        return True
    except Exception as e:
        logger.error(f"Error in download_artworks_by_member_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        __job_sleep()

@pixiv_worker.task(name="download_artworks_by_tag", queue='pixivutil-queue')
def download_artworks_by_tag(request_dict: dict):
    try:
        request = DownloadArtworksByTagsRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log("info", f"Downloading artwork by tag: {request.tags}. Bookmark minimum: {request.bookmark_count}")
        PixivServer.service.pixiv.service.download_artworks_by_tag(request)
        return True
    except Exception as e:
        logger.error(f"Error in download_artworks_by_tag worker: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        __job_sleep()

@pixiv_worker.task(name="delete_artwork_by_id", queue='pixivutil-queue')
def delete_artwork_by_id(request_dict: dict):
    try:
        request = DeleteArtworkByIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log("info", f"Deleting artwork by ID: {request.artwork_id}.")
        PixivServer.service.pixiv.service.delete_artwork_by_id(request)
        return True
    except Exception as e:
        logger.error(f"Error in delete_artwork_by_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        __job_sleep()


@pixiv_worker.task(name="download_member_metadata_by_id", queue='pixivutil-queue')
def download_member_metadata_by_id(request_dict: dict):
    try:
        request = DownloadMemberMetadataByIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log(
            "info",
            f"Downloading member metadata by ID: {request.member_id}.",
        )
        PixivServer.service.pixiv.service.download_member_metadata_by_id(request)
        return True
    except Exception as e:
        logger.error(f"Error in download_member_metadata_by_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        __job_sleep()


@pixiv_worker.task(name="download_artwork_metadata_by_id", queue='pixivutil-queue')
def download_artwork_metadata_by_id(request_dict: dict):
    try:
        request = DownloadArtworkMetadataByIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log(
            "info",
            f"Downloading artwork metadata by ID: {request.artwork_id}.",
        )
        PixivServer.service.pixiv.service.download_artwork_metadata_by_id(request)
        return True
    except Exception as e:
        logger.error(f"Error in download_artwork_metadata_by_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        __job_sleep()


@pixiv_worker.task(name="download_series_metadata_by_id", queue='pixivutil-queue')
def download_series_metadata_by_id(request_dict: dict):
    try:
        request = DownloadSeriesMetadataByIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log(
            "info",
            f"Downloading series metadata by ID: {request.series_id}.",
        )
        PixivServer.service.pixiv.service.download_series_metadata_by_id(request)
        return True
    except Exception as e:
        logger.error(f"Error in download_series_metadata_by_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        __job_sleep()


@pixiv_worker.task(name="download_tag_metadata_by_id", queue='pixivutil-queue')
def download_tag_metadata_by_id(request_dict: dict):
    try:
        request = DownloadTagMetadataByIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log(
            "info",
            f"Downloading tag metadata: {request.tag} (filter_mode={request.filter_mode}).",
        )
        PixivServer.service.pixiv.service.download_tag_metadata_by_id(request)
        return True
    except Exception as e:
        logger.error(f"Error in download_tag_metadata_by_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        __job_sleep()
