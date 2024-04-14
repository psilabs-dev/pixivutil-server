from pydantic import BaseModel

class NotificationRequest(BaseModel):
    message: str
