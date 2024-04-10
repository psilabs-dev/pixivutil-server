from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
import logging
import time

from PixivServer.service import pixiv
from PixivServer.router import download, health, metadata, server

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    # startup actions
    pixiv.service.open()
    yield
    # shutdown actions
    pixiv.service.close()

logger.info("Setting 10s pause for rabbitmq startup...")
# time.sleep(10)
logger.info("Starting PixivUtil Server...")
app = FastAPI(
    lifespan=lifespan
)

app.include_router(health.router)
app.include_router(metadata.router)
app.include_router(download.router)
app.include_router(server.router)

@app.get("/")
async def info():
    with open("VERSION", "r") as reader:
        version = reader.read().strip()
    return Response(
        content=f"PixivUtil Server {version}",
        status_code=200
    )