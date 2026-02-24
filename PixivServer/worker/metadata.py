import logging
import random
import time
import traceback

from celery import shared_task

import PixivServer.service.pixiv
from PixivServer.models.pixiv_worker import (
    DownloadArtworkMetadataByIdRequest,
    DownloadMemberMetadataByIdRequest,
    DownloadSeriesMetadataByIdRequest,
    DownloadTagMetadataByIdRequest,
)

logger = logging.getLogger(__name__)


def __job_sleep():
    time.sleep(random.uniform(1, 5))
    return 0


@shared_task(name="download_member_metadata_by_id", queue='pixivutil-queue')
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


@shared_task(name="download_artwork_metadata_by_id", queue='pixivutil-queue')
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


@shared_task(name="download_series_metadata_by_id", queue='pixivutil-queue')
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


@shared_task(name="download_tag_metadata_by_id", queue='pixivutil-queue')
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
