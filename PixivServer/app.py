from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
import logging
import time

import PixivServer
import PixivServer.client
import PixivServer.client.notification
from PixivServer.service import *
from PixivServer.router import *

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    # startup actions
    time.sleep(5)
    pixiv_service.open()
    subscription_service.open()
    PixivServer.client.notification.send_notification('Pixiv server started.')
    yield
    # shutdown actions
    PixivServer.client.notification.send_notification('Pixiv server is shutting down.')
    pixiv_service.close()
    subscription_service.close()

logger.info("Starting PixivUtil Server...")
app = FastAPI(
    lifespan=lifespan
)

app.include_router(
    health_router,
    prefix="/api/health"
)
app.include_router(
    meta_router,
    prefix="/api/metadata"
)
app.include_router(
    download_router,
    prefix="/api/download"
)
app.include_router(
    server_router,
    prefix="/api/server"
)
app.include_router(
    subscription_router,
    prefix="/api/subscription"
)

@app.get("/")
async def info():
    with open("VERSION", "r") as reader:
        version = reader.read().strip()
    return Response(
        content=f"PixivUtil Server {version}",
        status_code=200
    )