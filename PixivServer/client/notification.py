import logging
import requests

from PixivServer.config.notification import config as notification_config

logger = logging.getLogger(__name__)

def send_notification(message: str):
    """
    Send a notification request to the notification server.
    """
    url = f'http://{notification_config.notification_host}/api/notification/send'
    data = {
        'message': message
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=data, headers=headers)
    return response
