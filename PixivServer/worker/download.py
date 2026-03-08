import logging
import traceback

from celery import shared_task

import PixivServer.service.pixiv
from PixivServer.config.celery import MAIN_QUEUE_NAME
from PixivServer.models.pixiv_worker import (
    DeleteArtworkByIdRequest,
    DownloadArtworkByIdRequest,
    DownloadArtworksByMemberIdRequest,
    DownloadArtworksByTagsRequest,
    as_celery_task,
)
from PixivServer.worker.common import (
    NETWORK_MAX_RETRIES,
    NETWORK_RETRY_COUNTDOWN,
    is_network_exception,
    job_sleep,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="download_artworks_by_id", queue=MAIN_QUEUE_NAME, max_retries=NETWORK_MAX_RETRIES)
def download_artworks_by_id(self, request_dict: dict):
    try:
        request = DownloadArtworkByIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log("info", f"Downloading artwork by ID: {request.artwork_id}.")
        PixivServer.service.pixiv.service.download_artwork_by_id(request)
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error in download_artworks_by_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        if is_network_exception(e):
            raise self.retry(exc=e, countdown=NETWORK_RETRY_COUNTDOWN)
        # TODO: non-network errors return False (acked as SUCCESS) to avoid DLQ routing.
        # Use per-task acks_on_failure_or_timeout=True + Reject(requeue=False) for network
        # exhaustion so non-network errors can raise normally and show as FAILURE.
        return False
    finally:
        job_sleep()


@shared_task(bind=True, name="download_artworks_by_member_id", queue=MAIN_QUEUE_NAME, max_retries=NETWORK_MAX_RETRIES)
def download_artworks_by_member_id(self, request_dict: dict):
    try:
        request = DownloadArtworksByMemberIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log("info", f"Downloading artworks by member ID: {request.member_id}.")
        PixivServer.service.pixiv.service.download_artworks_by_member_id(request)
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error in download_artworks_by_member_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        if is_network_exception(e):
            raise self.retry(exc=e, countdown=NETWORK_RETRY_COUNTDOWN)
        # TODO: see download_artworks_by_id for non-network error handling fix.
        return False
    finally:
        job_sleep()


@shared_task(bind=True, name="download_artworks_by_tag", queue=MAIN_QUEUE_NAME, max_retries=NETWORK_MAX_RETRIES)
def download_artworks_by_tag(self, request_dict: dict):
    try:
        request = DownloadArtworksByTagsRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log("info", f"Downloading artwork by tag: {request.tags}. Bookmark minimum: {request.bookmark_count}")
        PixivServer.service.pixiv.service.download_artworks_by_tag(request)
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error in download_artworks_by_tag worker: {str(e)}")
        logger.error(traceback.format_exc())
        if is_network_exception(e):
            raise self.retry(exc=e, countdown=NETWORK_RETRY_COUNTDOWN)
        # TODO: see download_artworks_by_id for non-network error handling fix.
        return False
    finally:
        job_sleep()


@shared_task(bind=True, name="delete_artwork_by_id", queue=MAIN_QUEUE_NAME, max_retries=NETWORK_MAX_RETRIES)
def delete_artwork_by_id(self, request_dict: dict):
    try:
        request = DeleteArtworkByIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log("info", f"Deleting artwork by ID: {request.artwork_id}.")
        PixivServer.service.pixiv.service.delete_artwork_by_id(request)
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error in delete_artwork_by_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        if is_network_exception(e):
            raise self.retry(exc=e, countdown=NETWORK_RETRY_COUNTDOWN)
        # TODO: see download_artworks_by_id for non-network error handling fix.
        return False
    finally:
        job_sleep()


download_artworks_by_id_task = as_celery_task(download_artworks_by_id)
download_artworks_by_member_id_task = as_celery_task(download_artworks_by_member_id)
download_artworks_by_tag_task = as_celery_task(download_artworks_by_tag)
delete_artwork_by_id_task = as_celery_task(delete_artwork_by_id)
