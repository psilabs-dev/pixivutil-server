import logging
import random
import time
import traceback
from urllib.error import URLError

from celery import shared_task

import PixivServer.service.pixiv
from PixivServer.config.celery import MAIN_QUEUE_NAME
from PixivServer.models.pixiv_worker import (
    DeleteArtworkByIdRequest,
    DownloadArtworkByIdRequest,
    DownloadArtworksByMemberIdRequest,
    DownloadArtworksByTagsRequest,
)
from PixivServer.service.pixiv import PixivException

logger = logging.getLogger(__name__)

_NETWORK_MAX_RETRIES = 3
_NETWORK_RETRY_COUNTDOWN = 60


def __job_sleep():
    time.sleep(random.uniform(1, 5))
    return 0


def _is_network_exception(exc: BaseException) -> bool:
    if isinstance(exc, PixivException):
        return exc.errorCode in (PixivException.DOWNLOAD_FAILED_NETWORK, PixivException.SERVER_ERROR)
    return isinstance(exc, (ConnectionError, TimeoutError, URLError))


@shared_task(bind=True, name="download_artworks_by_id", queue=MAIN_QUEUE_NAME, max_retries=_NETWORK_MAX_RETRIES)
def download_artworks_by_id(self, request_dict: dict):
    try:
        request = DownloadArtworkByIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log("info", f"Downloading artwork by ID: {request.artwork_id}.")
        PixivServer.service.pixiv.service.download_artwork_by_id(request)
        return True
    except Exception as e:
        logger.error(f"Error in download_artworks_by_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        if _is_network_exception(e):
            raise self.retry(exc=e, countdown=_NETWORK_RETRY_COUNTDOWN)
        return False
    finally:
        __job_sleep()


@shared_task(bind=True, name="download_artworks_by_member_id", queue=MAIN_QUEUE_NAME, max_retries=_NETWORK_MAX_RETRIES)
def download_artworks_by_member_id(self, request_dict: dict):
    try:
        request = DownloadArtworksByMemberIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log("info", f"Downloading artworks by member ID: {request.member_id}.")
        PixivServer.service.pixiv.service.download_artworks_by_member_id(request)
        return True
    except Exception as e:
        logger.error(f"Error in download_artworks_by_member_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        if _is_network_exception(e):
            raise self.retry(exc=e, countdown=_NETWORK_RETRY_COUNTDOWN)
        return False
    finally:
        __job_sleep()


@shared_task(bind=True, name="download_artworks_by_tag", queue=MAIN_QUEUE_NAME, max_retries=_NETWORK_MAX_RETRIES)
def download_artworks_by_tag(self, request_dict: dict):
    try:
        request = DownloadArtworksByTagsRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log("info", f"Downloading artwork by tag: {request.tags}. Bookmark minimum: {request.bookmark_count}")
        PixivServer.service.pixiv.service.download_artworks_by_tag(request)
        return True
    except Exception as e:
        logger.error(f"Error in download_artworks_by_tag worker: {str(e)}")
        logger.error(traceback.format_exc())
        if _is_network_exception(e):
            raise self.retry(exc=e, countdown=_NETWORK_RETRY_COUNTDOWN)
        return False
    finally:
        __job_sleep()


@shared_task(bind=True, name="delete_artwork_by_id", queue=MAIN_QUEUE_NAME, max_retries=_NETWORK_MAX_RETRIES)
def delete_artwork_by_id(self, request_dict: dict):
    try:
        request = DeleteArtworkByIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log("info", f"Deleting artwork by ID: {request.artwork_id}.")
        PixivServer.service.pixiv.service.delete_artwork_by_id(request)
        return True
    except Exception as e:
        logger.error(f"Error in delete_artwork_by_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        if _is_network_exception(e):
            raise self.retry(exc=e, countdown=_NETWORK_RETRY_COUNTDOWN)
        return False
    finally:
        __job_sleep()
