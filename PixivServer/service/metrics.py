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
from pathlib import Path
from urllib.parse import quote, urlparse

import psutil

import PixivServer

# import PixivServer.routers.subscription
import PixivServer.service
import PixivServer.service.pixiv
from PixivServer.config.celery import DEAD_LETTER_QUEUE_NAME, MAIN_QUEUE_NAME
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
    DLQ_DEPTH,
    QUEUE_DEPTH,
    SYS_CPU_PERCENT,
    SYS_DISK_TOTAL_BYTES,
    SYS_DISK_USED_BYTES,
    SYS_MEM_TOTAL_BYTES,
    SYS_MEM_USED_BYTES,
)
from PixivServer.repository.pixivutil import PixivUtilRepository

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


def _rabbitmq_queue_message_count(queue_name: str) -> int | None:
    parsed_mgmt = urlparse(rabbitmq_config.management_url)
    user = parsed_mgmt.username or "guest"
    password = parsed_mgmt.password or "guest"
    base = f"{parsed_mgmt.scheme}://{parsed_mgmt.hostname}"
    if parsed_mgmt.port:
        base = f"{base}:{parsed_mgmt.port}"
    parsed_broker = urlparse(rabbitmq_config.broker_url)
    raw_vhost = parsed_broker.path.lstrip("/")
    vhost = raw_vhost if raw_vhost else "/"
    encoded_vhost = quote(vhost, safe="")
    url = f"{base}/api/queues/{encoded_vhost}/{queue_name}"
    credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {credentials}"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return int(data.get("messages", 0))
    except (urllib.error.URLError, OSError, ValueError):
        return None  # Management API unavailable


def _collect_queue_depth() -> None:
    count = _rabbitmq_queue_message_count(MAIN_QUEUE_NAME)
    if count is not None:
        QUEUE_DEPTH.set(count)


def _collect_dlq_depth() -> None:
    count = _rabbitmq_queue_message_count(DEAD_LETTER_QUEUE_NAME)
    if count is not None:
        DLQ_DEPTH.set(count)


async def periodic_metrics_collector() -> None:
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
                await asyncio.to_thread(_collect_dlq_depth)
                last_queue = time.monotonic()
        except Exception:  # noqa: BLE001
            logger.warning(f"Metrics collector error: {traceback.format_exc()}")
        await asyncio.sleep(1)
