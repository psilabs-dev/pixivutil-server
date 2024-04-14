import abc

class NotificationClient(abc.ABC):

    @abc.abstractmethod
    def send_notification(self, message: str):
        """
        Send a notification.
        """
        ...

    @classmethod
    @abc.abstractmethod
    def is_available(self) -> bool:
        """
        Check whether the configurations to set up a notification client is available.
        """
        ...