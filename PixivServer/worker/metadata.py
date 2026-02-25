import logging
import random
import time
import traceback
from urllib.error import URLError

from celery import shared_task

import PixivServer.service.pixiv
from PixivServer.config.celery import MAIN_QUEUE_NAME
from PixivServer.models.pixiv_worker import (
    DownloadArtworkMetadataByIdRequest,
    DownloadMemberMetadataByIdRequest,
    DownloadSeriesMetadataByIdRequest,
    DownloadTagMetadataByIdRequest,
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


@shared_task(bind=True, name="download_member_metadata_by_id", queue=MAIN_QUEUE_NAME, max_retries=_NETWORK_MAX_RETRIES)
def download_member_metadata_by_id(self, request_dict: dict):
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
        if _is_network_exception(e):
            raise self.retry(exc=e, countdown=_NETWORK_RETRY_COUNTDOWN)
        return False
    finally:
        __job_sleep()


@shared_task(bind=True, name="download_artwork_metadata_by_id", queue=MAIN_QUEUE_NAME, max_retries=_NETWORK_MAX_RETRIES)
def download_artwork_metadata_by_id(self, request_dict: dict):
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
        if _is_network_exception(e):
            raise self.retry(exc=e, countdown=_NETWORK_RETRY_COUNTDOWN)
        return False
    finally:
        __job_sleep()


@shared_task(bind=True, name="download_series_metadata_by_id", queue=MAIN_QUEUE_NAME, max_retries=_NETWORK_MAX_RETRIES)
def download_series_metadata_by_id(self, request_dict: dict):
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
        if _is_network_exception(e):
            raise self.retry(exc=e, countdown=_NETWORK_RETRY_COUNTDOWN)
        return False
    finally:
        __job_sleep()


@shared_task(bind=True, name="download_tag_metadata_by_id", queue=MAIN_QUEUE_NAME, max_retries=_NETWORK_MAX_RETRIES)
def download_tag_metadata_by_id(self, request_dict: dict):
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
        if _is_network_exception(e):
            raise self.retry(exc=e, countdown=_NETWORK_RETRY_COUNTDOWN)
        return False
    finally:
        __job_sleep()
