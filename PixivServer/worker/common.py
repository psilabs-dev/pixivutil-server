import random
import time
from urllib.error import URLError

from PixivServer.service.pixiv import PixivException

NETWORK_MAX_RETRIES = 3
NETWORK_RETRY_COUNTDOWN = 60


def job_sleep():
    time.sleep(random.uniform(1, 5))
    return 0


def is_network_exception(exc: BaseException) -> bool:
    if isinstance(exc, PixivException):
        return exc.errorCode in (PixivException.DOWNLOAD_FAILED_NETWORK, PixivException.SERVER_ERROR)
    return isinstance(exc, (ConnectionError, TimeoutError, URLError))
