import logging
from fastapi import APIRouter, Response

from PixivServer.model.notification import NotificationRequest
from PixivServer.notification import send_notification

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post('/send')
async def server_send_notification(notification: NotificationRequest):
    """
    Send notification.
    """
    await send_notification(notification.message)
    return Response('success')
