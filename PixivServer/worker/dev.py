import logging
import random
import time
import traceback

from celery import shared_task

import PixivServer.service.pixiv
from PixivServer.models.pixiv_worker import DownloadArtworkByIdRequest

logger = logging.getLogger(__name__)


def __job_sleep():
    time.sleep(random.uniform(1, 5))
    return 0


@shared_task(name="dev_download_artworks_by_id", queue='pixivutil-queue')
def dev_download_artworks_by_id(request_dict: dict):
    try:
        request = DownloadArtworkByIdRequest(**request_dict)
        PixivServer.service.pixiv.PixivHelper.print_and_log("info", f"(test) Downloading artwork by ID: {request.artwork_id}.")
        time.sleep(3)
        PixivServer.service.pixiv.PixivHelper.print_and_log("info", f"(test) Completed download artwork by ID: {request.artwork_id}.")
        return True
    except Exception as e:
        logger.error(f"Error in download_artworks_by_id worker: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        __job_sleep()
