import logging
from pathlib import Path

from celery import shared_task

from PixivServer.models.pixiv_worker import DownloadArtworkByIdRequest

logger = logging.getLogger(__name__)

_SIMULATED_RETRY_COUNTDOWN = 1
_SIMULATED_MAX_RETRIES = 1
_SUCCESS_SENTINEL_PATH = Path("/tmp/pixivutil-dev-dlq-success.flag")

# This endpoint exists to confirm DLQ functionality.
# Use this for any kind of DLQ-related task and make any necessary changes in logic to prove/confirm hypotheses.
# This will be commented out once DLQ is stable, so in the meantime do whatever you want with this endpoint,
# just clean it up when done and don't commit things back in.
@shared_task(bind=True, name="dev_download_artworks_by_id", queue='pixivutil-queue')
def dev_download_artworks_by_id(self, request_dict: dict):
    request = DownloadArtworkByIdRequest(**request_dict)
    attempt = self.request.retries + 1
    max_attempts = _SIMULATED_MAX_RETRIES + 1
    logger.error(f"(dev) Attempt {attempt}/{max_attempts} for artwork_id={request.artwork_id}")
    if attempt < max_attempts:
        raise self.retry(
            exc=ConnectionError("Simulated network failure"),
            countdown=_SIMULATED_RETRY_COUNTDOWN,
        )
    if _SUCCESS_SENTINEL_PATH.exists():
        logger.error(f"(dev) Sentinel found at {_SUCCESS_SENTINEL_PATH}; succeeding on resumed run")
        return True
    logger.error(f"(dev) Max retries exceeded for artwork_id={request.artwork_id}, raising terminal failure for broker DLQ")
    raise ConnectionError("Simulated terminal failure after retries")
