import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse
from kombu import Connection

from PixivServer.config import rabbitmq
from PixivServer.config.celery import dead_letter_queue, default_exchange
from PixivServer.worker import pixiv_worker

logger = logging.getLogger('uvicorn.pixivutil')
router = APIRouter()


def _extract_task_payload_from_celery_body(body: Any) -> dict:
    # Celery protocol v2 JSON body is typically [args, kwargs, embed].
    if not isinstance(body, list) or len(body) < 2:
        return {}
    args = body[0]
    kwargs = body[1]
    if isinstance(args, list) and len(args) == 1 and isinstance(args[0], dict):
        return args[0]
    if isinstance(kwargs, dict) and "request_dict" in kwargs and isinstance(kwargs["request_dict"], dict):
        return kwargs["request_dict"]
    if isinstance(kwargs, dict):
        return kwargs
    return {}


def _normalize_dead_letter_payload(body: Any, headers: dict | None = None) -> dict | None:
    if isinstance(body, dict):
        if "dead_letter_id" in body and "task_name" in body:
            return {
                "dead_letter_id": str(body["dead_letter_id"]),
                "task_name": str(body["task_name"]),
                "payload": body.get("payload", {}) if isinstance(body.get("payload", {}), dict) else {},
            }
        if "task_name" in body and "payload" in body:
            # Backfill a stable identifier for older custom format if present.
            return {
                "dead_letter_id": str(body.get("dead_letter_id") or body.get("task_id") or ""),
                "task_name": str(body["task_name"]),
                "payload": body.get("payload", {}) if isinstance(body.get("payload", {}), dict) else {},
            }

    headers = headers or {}
    task_name = headers.get("task")
    task_id = headers.get("id") or headers.get("task_id")
    if isinstance(task_name, str):
        return {
            "dead_letter_id": str(task_id or ""),
            "task_name": task_name,
            "payload": _extract_task_payload_from_celery_body(body),
        }
    return None


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


def _kombu_message_to_dlq_record(msg) -> dict | None:
    headers = msg.headers if isinstance(msg.headers, dict) else {}
    return _normalize_dead_letter_payload(msg.payload, headers=headers)


def _get_registered_task(task_name: str | None):
    if not task_name:
        return None
    # Skip Celery internals/builtins even if registered.
    if task_name.startswith("celery."):
        return None
    task = pixiv_worker.tasks.get(task_name)
    return task if task is not None else None


def _is_native_celery_message(msg) -> bool:
    headers = msg.headers if isinstance(msg.headers, dict) else {}
    return isinstance(headers.get("task"), str)


def _clean_republish_headers(headers: dict) -> dict:
    # Drop broker-added dead-letter metadata so replayed messages don't keep stale x-death history.
    ignored = {
        "x-death",
        "x-first-death-exchange",
        "x-first-death-queue",
        "x-first-death-reason",
        "x-last-death-exchange",
        "x-last-death-queue",
        "x-last-death-reason",
    }
    return {k: v for k, v in headers.items() if k not in ignored}


def _republish_native_celery_message(conn, msg) -> str | None:
    if not _is_native_celery_message(msg):
        return None

    headers = msg.headers if isinstance(msg.headers, dict) else {}
    task_name = headers.get("task")
    if not isinstance(task_name, str):
        return None

    props = msg.properties if isinstance(msg.properties, dict) else {}
    publish_props = {}
    for key in (
        "correlation_id",
        "reply_to",
        "priority",
        "expiration",
        "message_id",
        "timestamp",
        "type",
        "app_id",
    ):
        value = props.get(key)
        if value is not None:
            publish_props[key] = value

    with conn.Producer() as producer:
        raw_body = msg.body
        if isinstance(raw_body, str):
            raw_body = raw_body.encode(msg.content_encoding or "utf-8")
        if isinstance(raw_body, memoryview):
            raw_body = raw_body.tobytes()
        producer.publish(
            raw_body,
            exchange=default_exchange,
            routing_key="pixivutil-queue",
            headers=_clean_republish_headers(headers),
            content_type=msg.content_type,
            content_encoding=msg.content_encoding,
            delivery_mode=2,
            **publish_props,
        )
    return task_name


def _resume_message(conn, msg, body: dict) -> str | None:
    task_name = _republish_native_celery_message(conn, msg)
    if task_name is not None:
        return task_name

    task_fn = _get_registered_task(body.get("task_name"))
    if task_fn is None:
        return None
    task_fn.delay(body.get("payload", {}))
    return body.get("task_name")


@router.get("/")
async def list_dead_letter_messages() -> Response:
    """
    List all messages currently in the dead letter queue.
    """
    def _run() -> list[dict]:
        messages: list[dict] = []
        with Connection(rabbitmq.config.broker_url) as conn:
            for msg in _drain(conn):
                try:
                    normalized = _kombu_message_to_dlq_record(msg)
                    if normalized is not None:
                        messages.append(normalized)
                finally:
                    msg.reject(requeue=True)
        return messages

    return JSONResponse(await asyncio.to_thread(_run))


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
                body = _kombu_message_to_dlq_record(msg)
                if body is None:
                    logger.warning("Unparseable DLQ message, leaving in queue")
                    msg.reject(requeue=True)
                    continue
                resumed_task_name = _resume_message(conn, msg, body)
                if resumed_task_name is not None:
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
                body = _kombu_message_to_dlq_record(msg)
                if body is None:
                    msg.reject(requeue=True)
                    continue
                if body.get("dead_letter_id") == dead_letter_id:
                    resumed_task_name = _resume_message(conn, msg, body)
                    if resumed_task_name is None:
                        msg.reject(requeue=True)
                        return "unknown"
                    msg.ack()
                    return resumed_task_name
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
                body = _kombu_message_to_dlq_record(msg)
                if body is None:
                    msg.reject(requeue=True)
                    continue
                if body.get("dead_letter_id") == dead_letter_id:
                    msg.ack()
                    return True
                msg.reject(requeue=True)
        return False

    found = await asyncio.to_thread(_run)
    if not found:
        raise HTTPException(status_code=404, detail=f"Dead letter message not found: {dead_letter_id}")
    return JSONResponse({"dead_letter_id": dead_letter_id, "dropped": True})
