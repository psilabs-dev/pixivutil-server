import asyncio
import logging
import time
import traceback
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, Response

import PixivServer
import PixivServer.auth
import PixivServer.routers
import PixivServer.routers.database
import PixivServer.routers.download_queue
import PixivServer.routers.health
import PixivServer.routers.metadata_queue
import PixivServer.routers.metrics
import PixivServer.routers.server

# import PixivServer.routers.subscription
import PixivServer.service
import PixivServer.service.pixiv
from PixivServer.config.server import config as server_config
from PixivServer.metrics import (
    HTTP_REQUEST_DURATION,
    HTTP_REQUEST_SIZE,
    HTTP_REQUESTS_TOTAL,
    HTTP_RESPONSE_SIZE,
    SERVER_INFO,
)
from PixivServer.service.metrics import periodic_metrics_collector
from PixivServer.utils import get_version

logger = logging.getLogger('uvicorn.pixivutil')

@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        logger.info(f"Setting up server in {server_config.server_env} environment.")

        # startup actions
        await asyncio.sleep(5)
        PixivServer.service.pixiv.service.open(validate_pixiv_login=False)
        SERVER_INFO.info({"version": get_version()})
        # PixivServer.service.subscription_service.open()
    except Exception as e:
        print(f"Encountered exception during application setup: {traceback.format_exc()}")
        raise e
    collector_task = asyncio.create_task(periodic_metrics_collector())
    yield
    # shutdown actions
    collector_task.cancel()
    await asyncio.gather(collector_task, return_exceptions=True)
    PixivServer.service.pixiv.service.close()
    # PixivServer.service.subscription_service.close()

logger.info("Starting PixivUtil Server...")
app = FastAPI(
    lifespan=lifespan
)

auth_dependency = [Depends(PixivServer.auth.is_valid_api_key_header)]


@app.middleware("http")
async def request_metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    route = request.scope.get("route")
    endpoint = route.path if route and hasattr(route, "path") else None
    if endpoint is None:
        return response
    status_class = f"{response.status_code // 100}xx"
    req_size = int(request.headers.get("content-length", 0))
    resp_size = int(response.headers.get("content-length", 0))

    HTTP_REQUESTS_TOTAL.labels(request.method, endpoint, status_class).inc()
    HTTP_REQUEST_DURATION.labels(request.method, endpoint).observe(duration)
    HTTP_REQUEST_SIZE.labels(request.method, endpoint).observe(req_size)
    HTTP_RESPONSE_SIZE.labels(request.method, endpoint).observe(resp_size)
    return response


app.include_router(
    PixivServer.routers.health.router,
    prefix="/api/health",
)
app.include_router(
    PixivServer.routers.metrics.router,
    prefix="/metrics",
    dependencies=auth_dependency,
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

if server_config.server_env == 'development':
    import PixivServer.routers.dev
    app.include_router(
        PixivServer.routers.dev.router,
        prefix="/api/dev",
        dependencies=auth_dependency,
    )


@app.get("/")
async def info():
    return Response(content=f"PixivUtil Server {get_version()}", status_code=200)
