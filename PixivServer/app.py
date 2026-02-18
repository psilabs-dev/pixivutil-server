import asyncio
import base64
import contextlib
import json
import logging
import os
import time
import traceback
import urllib.error
import urllib.request
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote, urlparse

import psutil
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
from PixivServer.config.pixivutil import config as pixivutil_config
from PixivServer.config.rabbitmq import config as rabbitmq_config
from PixivServer.metrics import (
    DB_ARTWORKS,
    DB_MEMBERS,
    DB_PAGES,
    DB_SERIES,
    DB_TAGS,
    DISK_DATABASE_BYTES,
    DISK_DOWNLOADS_BYTES,
    HTTP_REQUEST_DURATION,
    HTTP_REQUEST_SIZE,
    HTTP_REQUESTS_TOTAL,
    HTTP_RESPONSE_SIZE,
    QUEUE_DEPTH,
    SERVER_INFO,
    SYS_CPU_PERCENT,
    SYS_DISK_TOTAL_BYTES,
    SYS_DISK_USED_BYTES,
    SYS_MEM_TOTAL_BYTES,
    SYS_MEM_USED_BYTES,
)
from PixivServer.repository.pixivutil import PixivUtilRepository
from PixivServer.utils import get_version

logger = logging.getLogger('uvicorn.pixivutil')

_SYSTEM_COLLECT_INTERVAL = 15   # seconds
_DB_STAT_COLLECT_INTERVAL = 60  # seconds
_DISK_COLLECT_INTERVAL = 300    # seconds (directory walk may be slow on large collections)
_QUEUE_COLLECT_INTERVAL = 15    # seconds


def _collect_system_metrics() -> None:
    cpu = psutil.cpu_percent(interval=1)
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    SYS_CPU_PERCENT.set(cpu)
    SYS_MEM_USED_BYTES.set(vm.used)
    SYS_MEM_TOTAL_BYTES.set(vm.total)
    SYS_DISK_USED_BYTES.set(disk.used)
    SYS_DISK_TOTAL_BYTES.set(disk.total)


def _collect_db_stats() -> None:
    repo = PixivUtilRepository()
    repo.open()
    try:
        DB_MEMBERS.set(repo.count_members())
        DB_ARTWORKS.set(repo.count_artworks())
        DB_PAGES.set(repo.count_pages())
        DB_TAGS.set(repo.count_tags())
        DB_SERIES.set(repo.count_series())
    finally:
        repo.close()


def _collect_disk_metrics() -> None:
    # Database file + WAL/SHM sidecars
    db_path = pixivutil_config.db_path
    db_bytes = 0
    for suffix in ("", "-wal", "-shm"):
        p = db_path + suffix
        if os.path.isfile(p):
            db_bytes += os.path.getsize(p)
    DISK_DATABASE_BYTES.set(db_bytes)

    # Downloads directory — recursive file size sum
    downloads = Path(PixivServer.service.pixiv.service.downloads_folder)
    total = 0
    if downloads.is_dir():
        for f in downloads.rglob("*"):
            if f.is_file():
                with contextlib.suppress(OSError):
                    total += f.stat().st_size
    DISK_DOWNLOADS_BYTES.set(total)


def _collect_queue_depth() -> None:
    parsed = urlparse(rabbitmq_config.broker_url)
    user = parsed.username or "guest"
    password = parsed.password or "guest"
    host = parsed.hostname or "rabbitmq"
    raw_vhost = parsed.path.lstrip("/")
    vhost = raw_vhost if raw_vhost else "/"
    encoded_vhost = quote(vhost, safe="")
    url = f"http://{host}:15672/api/queues/{encoded_vhost}/pixivutil-queue"
    credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {credentials}"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            QUEUE_DEPTH.set(data.get("messages", 0))
    except (urllib.error.URLError, OSError, ValueError):
        pass  # Management API unavailable; leave metric stale


async def _periodic_metrics_collector() -> None:
    last_system = 0.0
    last_db = 0.0
    last_disk = 0.0
    last_queue = 0.0
    while True:
        now = time.monotonic()
        try:
            if now - last_system >= _SYSTEM_COLLECT_INTERVAL:
                await asyncio.to_thread(_collect_system_metrics)
                last_system = time.monotonic()
            if now - last_db >= _DB_STAT_COLLECT_INTERVAL:
                await asyncio.to_thread(_collect_db_stats)
                last_db = time.monotonic()
            if now - last_disk >= _DISK_COLLECT_INTERVAL:
                await asyncio.to_thread(_collect_disk_metrics)
                last_disk = time.monotonic()
            if now - last_queue >= _QUEUE_COLLECT_INTERVAL:
                await asyncio.to_thread(_collect_queue_depth)
                last_queue = time.monotonic()
        except Exception:  # noqa: BLE001
            logger.warning(f"Metrics collector error: {traceback.format_exc()}")
        await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        logger.info("Setting up server.")
        # startup actions
        asyncio.sleep(5)
        PixivServer.service.pixiv.service.open(validate_pixiv_login=False)
        SERVER_INFO.info({"version": get_version()})
        # PixivServer.service.subscription_service.open()
    except Exception as e:
        print(f"Encountered exception during application setup: {traceback.format_exc()}")
        raise e
    collector_task = asyncio.create_task(_periodic_metrics_collector())
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


@app.get("/")
async def info():
    return Response(content=f"PixivUtil Server {get_version()}", status_code=200)
