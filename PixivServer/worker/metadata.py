import logging
import traceback

from celery import shared_task

import PixivServer.service.pixiv
from PixivServer.config.celery import MAIN_QUEUE_NAME
from PixivServer.models.pixiv_worker import (
    DownloadArtworkMetadataByIdRequest,
    DownloadMemberMetadataByIdRequest,
    DownloadSeriesMetadataByIdRequest,
    DownloadTagMetadataByIdRequest,
    as_celery_task,
)
from PixivServer.worker.common import (
    NETWORK_MAX_RETRIES,
    NETWORK_RETRY_COUNTDOWN,
    is_network_exception,
    job_sleep,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="download_member_metadata_by_id", queue=MAIN_QUEUE_NAME, max_retries=NETWORK_MAX_RETRIES)
def download_member_metadata_by_id(self, request_dict: dict):
    try:
        request = DownloadMemberMetadataByIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log(
            "info",
            f"Downloading member metadata by ID: {request.member_id}.",
        )
        PixivServer.service.pixiv.service.download_member_metadata_by_id(request)
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error in download_member_metadata_by_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        if is_network_exception(e):
            raise self.retry(exc=e, countdown=NETWORK_RETRY_COUNTDOWN)
        # TODO: non-network errors return False (acked as SUCCESS) to avoid DLQ routing.
        # Use per-task acks_on_failure_or_timeout=True + Reject(requeue=False) for network
        # exhaustion so non-network errors can raise normally and show as FAILURE.
        return False
    finally:
        job_sleep()


@shared_task(bind=True, name="download_artwork_metadata_by_id", queue=MAIN_QUEUE_NAME, max_retries=NETWORK_MAX_RETRIES)
def download_artwork_metadata_by_id(self, request_dict: dict):
    try:
        request = DownloadArtworkMetadataByIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log(
            "info",
            f"Downloading artwork metadata by ID: {request.artwork_id}.",
        )
        PixivServer.service.pixiv.service.download_artwork_metadata_by_id(request)
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error in download_artwork_metadata_by_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        if is_network_exception(e):
            raise self.retry(exc=e, countdown=NETWORK_RETRY_COUNTDOWN)
        # TODO: see download_member_metadata_by_id for non-network error handling fix.
        return False
    finally:
        job_sleep()


@shared_task(bind=True, name="download_series_metadata_by_id", queue=MAIN_QUEUE_NAME, max_retries=NETWORK_MAX_RETRIES)
def download_series_metadata_by_id(self, request_dict: dict):
    try:
        request = DownloadSeriesMetadataByIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log(
            "info",
            f"Downloading series metadata by ID: {request.series_id}.",
        )
        PixivServer.service.pixiv.service.download_series_metadata_by_id(request)
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error in download_series_metadata_by_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        if is_network_exception(e):
            raise self.retry(exc=e, countdown=NETWORK_RETRY_COUNTDOWN)
        # TODO: see download_member_metadata_by_id for non-network error handling fix.
        return False
    finally:
        job_sleep()


@shared_task(bind=True, name="download_tag_metadata_by_id", queue=MAIN_QUEUE_NAME, max_retries=NETWORK_MAX_RETRIES)
def download_tag_metadata_by_id(self, request_dict: dict):
    try:
        request = DownloadTagMetadataByIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log(
            "info",
            f"Downloading tag metadata: {request.tag} (filter_mode={request.filter_mode}).",
        )
        PixivServer.service.pixiv.service.download_tag_metadata_by_id(request)
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error in download_tag_metadata_by_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        if is_network_exception(e):
            raise self.retry(exc=e, countdown=NETWORK_RETRY_COUNTDOWN)
        # TODO: see download_member_metadata_by_id for non-network error handling fix.
        return False
    finally:
        job_sleep()


download_member_metadata_by_id_task = as_celery_task(download_member_metadata_by_id)
download_artwork_metadata_by_id_task = as_celery_task(download_artwork_metadata_by_id)
download_series_metadata_by_id_task = as_celery_task(download_series_metadata_by_id)
download_tag_metadata_by_id_task = as_celery_task(download_tag_metadata_by_id)
