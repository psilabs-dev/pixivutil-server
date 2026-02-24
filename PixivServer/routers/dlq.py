import asyncio
import base64
import contextlib
import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse
from kombu import Connection

from PixivServer.config import rabbitmq
from PixivServer.config.celery import dead_letter_queue
from PixivServer.worker.download import (
    delete_artwork_by_id,
    download_artworks_by_id,
    download_artworks_by_member_id,
    download_artworks_by_tag,
)
from PixivServer.worker.metadata import (
    download_artwork_metadata_by_id,
    download_member_metadata_by_id,
    download_series_metadata_by_id,
    download_tag_metadata_by_id,
)

logger = logging.getLogger('uvicorn.pixivutil')
router = APIRouter()

_TASK_REGISTRY: dict = {
    "download_artworks_by_id": download_artworks_by_id,
    "download_artworks_by_member_id": download_artworks_by_member_id,
    "download_artworks_by_tag": download_artworks_by_tag,
    "delete_artwork_by_id": delete_artwork_by_id,
    "download_artwork_metadata_by_id": download_artwork_metadata_by_id,
    "download_member_metadata_by_id": download_member_metadata_by_id,
    "download_series_metadata_by_id": download_series_metadata_by_id,
    "download_tag_metadata_by_id": download_tag_metadata_by_id,
}


def _mgmt_get_messages(count: int = 100) -> list[dict]:
    parsed = urllib.parse.urlparse(rabbitmq.config.management_url)
    credentials = f"{parsed.username}:{parsed.password}"
    auth = base64.b64encode(credentials.encode()).decode()
    base_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
    url = f"{base_url}/api/queues/%2F/pixivutil-dead-letter/get"
    data = json.dumps({"count": count, "ackmode": "ack_requeue_true", "encoding": "auto"}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Basic {auth}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _drain(conn) -> list:
    bound = dead_letter_queue.bind(conn)
    bound.declare()
    msgs = []
    while True:
        msg = bound.get(no_ack=False)
        if msg is None:
            break
        msgs.append(msg)
    return msgs


@router.get("/")
async def list_dead_letter_messages() -> Response:
    """
    List all messages currently in the dead letter queue.
    """
    try:
        raw = await asyncio.to_thread(_mgmt_get_messages)
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=503, detail=f"RabbitMQ management API unavailable: {e}")
    messages = []
    for item in raw:
        with contextlib.suppress(KeyError, json.JSONDecodeError):
            messages.append(json.loads(item["payload"]))
    return JSONResponse(messages)


@router.post("/resume")
async def resume_all_dead_letter_messages() -> Response:
    """
    Requeue all dead letter messages to the main queue.
    Messages with unrecognised task names are left in the dead letter queue.
    """
    def _run() -> int:
        count = 0
        with Connection(rabbitmq.config.broker_url) as conn:
            for msg in _drain(conn):
                body = msg.payload
                task_fn = _TASK_REGISTRY.get(body.get("task_name"))
                if task_fn is not None:
                    task_fn.delay(body.get("payload", {}))
                    msg.ack()
                    count += 1
                else:
                    logger.warning(f"Unknown task name in DLQ message, leaving in queue: {body.get('task_name')}")
                    msg.reject(requeue=True)
        return count

    count = await asyncio.to_thread(_run)
    return JSONResponse({"requeued": count})


@router.post("/{dead_letter_id}/resume")
async def resume_dead_letter_message(dead_letter_id: str) -> Response:
    """
    Requeue a specific dead letter message to the main queue by its dead_letter_id.
    """
    def _run() -> str | None:
        """Returns task_name on success, None if not found, 'unknown' if task unrecognised."""
        with Connection(rabbitmq.config.broker_url) as conn:
            for msg in _drain(conn):
                body = msg.payload
                if body.get("dead_letter_id") == dead_letter_id:
                    task_fn = _TASK_REGISTRY.get(body.get("task_name"))
                    if task_fn is None:
                        msg.reject(requeue=True)
                        return "unknown"
                    task_fn.delay(body.get("payload", {}))
                    msg.ack()
                    return body.get("task_name")
                msg.reject(requeue=True)
        return None

    result = await asyncio.to_thread(_run)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Dead letter message not found: {dead_letter_id}")
    if result == "unknown":
        raise HTTPException(status_code=422, detail=f"Task name not recognised for dead letter message: {dead_letter_id}")
    return JSONResponse({"dead_letter_id": dead_letter_id, "requeued": True, "task_name": result})


@router.delete("/")
async def drop_all_dead_letter_messages() -> Response:
    """
    Purge all messages from the dead letter queue.
    """
    def _run() -> int:
        with Connection(rabbitmq.config.broker_url) as conn:
            return dead_letter_queue.bind(conn).purge()

    count = await asyncio.to_thread(_run)
    return JSONResponse({"dropped": count})


@router.delete("/{dead_letter_id}")
async def drop_dead_letter_message(dead_letter_id: str) -> Response:
    """
    Drop a specific dead letter message by its dead_letter_id.
    """
    def _run() -> bool:
        with Connection(rabbitmq.config.broker_url) as conn:
            for msg in _drain(conn):
                body = msg.payload
                if body.get("dead_letter_id") == dead_letter_id:
                    msg.ack()
                    return True
                msg.reject(requeue=True)
        return False

    found = await asyncio.to_thread(_run)
    if not found:
        raise HTTPException(status_code=404, detail=f"Dead letter message not found: {dead_letter_id}")
    return JSONResponse({"dead_letter_id": dead_letter_id, "dropped": True})
