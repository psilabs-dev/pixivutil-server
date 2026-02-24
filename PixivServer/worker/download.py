import logging
import random
import time
import traceback

from celery import shared_task

import PixivServer.service.pixiv
from PixivServer.models.pixiv_worker import (
    DeleteArtworkByIdRequest,
    DownloadArtworkByIdRequest,
    DownloadArtworksByMemberIdRequest,
    DownloadArtworksByTagsRequest,
)

logger = logging.getLogger(__name__)


def __job_sleep():
    time.sleep(random.uniform(1, 5))
    return 0


@shared_task(name="download_artworks_by_id", queue='pixivutil-queue')
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


@shared_task(name="download_artworks_by_member_id", queue='pixivutil-queue')
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


@shared_task(name="download_artworks_by_tag", queue='pixivutil-queue')
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


@shared_task(name="delete_artwork_by_id", queue='pixivutil-queue')
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
