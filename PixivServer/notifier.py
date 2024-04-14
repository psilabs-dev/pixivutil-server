from fastapi import FastAPI
import logging

from PixivServer.service import *
from PixivServer.router import *

logger = logging.getLogger(__name__)

logger.info("Starting PixivUtil Notification Server...")
app = FastAPI()

app.include_router(
    notification_router,
    prefix="/api/notification"
)
