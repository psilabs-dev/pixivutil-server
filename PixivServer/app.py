from contextlib import asynccontextmanager
import traceback
from PixivServer.utils import get_version
from fastapi import Depends, FastAPI, Response
import logging
import time

import PixivServer
import PixivServer.auth
import PixivServer.routers
import PixivServer.routers.database
import PixivServer.routers.download_queue
import PixivServer.routers.health
import PixivServer.routers.metadata_queue
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
        PixivServer.service.pixiv.service.open(validate_pixiv_login=False)
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

auth_dependency = [Depends(PixivServer.auth.is_valid_api_key_header)]

app.include_router(
    PixivServer.routers.health.router,
    prefix="/api/health"
)
app.include_router(
    PixivServer.routers.metadata_queue.router,
    prefix="/api/queue/metadata",
    dependencies=auth_dependency,
)
app.include_router(
    PixivServer.routers.download_queue.router,
    prefix="/api/queue/download",
    dependencies=auth_dependency,
)
app.include_router(
    PixivServer.routers.download_queue.router,
    prefix="/api/download",
    deprecated=True,
    dependencies=auth_dependency,
)
app.include_router(
    PixivServer.routers.server.router,
    prefix="/api/server",
    dependencies=auth_dependency,
)
app.include_router(
    PixivServer.routers.database.router,
    prefix="/api/database",
    dependencies=auth_dependency,
)
# app.include_router(
#     PixivServer.routers.subscription.router,
#     prefix="/api/subscription"
# )

@app.get("/")
async def info():
    return Response(content=f"PixivUtil Server {get_version()}", status_code=200)
