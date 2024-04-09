from matrix_client.client import MatrixClient

from PixivServer.client.notification.default import NotificationClient
from PixivServer.config import matrix

class MatrixNotificationClient(NotificationClient):

    def __init__(self):
        self.homeserver = f"https://{matrix.config.host}"
        self.room_id = matrix.config.room
        self.access_token = matrix.config.access_token

    def send_notification(self, message: str):
        client = MatrixClient(self.homeserver, token=self.access_token)
        room = client.join_room(self.room_id)
        room.send_text(message)

    @classmethod
    def is_available(self) -> bool:
        return matrix.config.access_token and matrix.config.host and matrix.config.room
