import logging
import traceback
from typing import List

from PixivServer.notification import default, matrix

logger = logging.getLogger(__name__)
clients: List[default.NotificationClient] = list()

if matrix.MatrixNotificationClient.is_available():
    clients.append(matrix.MatrixNotificationClient())

async def send_notification(message: str):
    for client in clients:
        try:
            client.send_notification(message)
        except Exception:
            logger.error(f"An error occurred while sending the notification {message}: ", traceback.format_exc())
    return message
