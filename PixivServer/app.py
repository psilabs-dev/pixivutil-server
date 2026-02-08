from contextlib import asynccontextmanager
import traceback
from PixivServer.utils import get_version
from fastapi import FastAPI, Response
import logging
import time

import PixivServer
import PixivServer.routers
import PixivServer.routers.database
import PixivServer.routers.download
import PixivServer.routers.health
import PixivServer.routers.metadata
import PixivServer.routers.server
# import PixivServer.routers.subscription
import PixivServer.service
import PixivServer.service.pixiv

logger = logging.getLogger('uvicorn.pixivutil')

@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        logger.info("Setting up server.")
        # startup actions
        time.sleep(5)
        PixivServer.service.pixiv.service.open()
        # PixivServer.service.subscription_service.open()
    except Exception as e:
        print(f"Encountered exception during application setup: {traceback.format_exc()}")
        raise e
    yield
    # shutdown actions
    PixivServer.service.pixiv.service.close()
    # PixivServer.service.subscription_service.close()

logger.info("Starting PixivUtil Server...")
app = FastAPI(
    lifespan=lifespan
)

app.include_router(
    PixivServer.routers.health.router,
    prefix="/api/health"
)
app.include_router(
    PixivServer.routers.metadata.router,
    prefix="/api/metadata"
)
app.include_router(
    PixivServer.routers.download.router,
    prefix="/api/download"
)
app.include_router(
    PixivServer.routers.server.router,
    prefix="/api/server"
)
app.include_router(
    PixivServer.routers.database.router,
    prefix="/api/database"
)
# app.include_router(
#     PixivServer.routers.subscription.router,
#     prefix="/api/subscription"
# )

@app.get("/")
async def info():
    return Response(content=f"PixivUtil Server {get_version()}", status_code=200)