import logging

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from PixivServer.config.celery import QUEUE_MAX_PRIORITY
from PixivServer.models.pixiv_worker import DownloadArtworkByIdRequest
from PixivServer.worker.dev import (
    dev_download_artworks_by_id,
    dev_priority_probe_task,
    get_dev_task_state,
    get_priority_probe_state,
)

logger = logging.getLogger('uvicorn.pixivutil')
router = APIRouter()


@router.post("/artwork/{artwork_id}")
async def dev_queue_download_artwork_by_id(artwork_id: str) -> Response:
    """
    (test) Download Pixiv image by ID.
    """
    logger.info(f"Downloading Pixiv artwork by image ID: {artwork_id}.")
    request = DownloadArtworkByIdRequest(artwork_id=int(artwork_id))
    artwork_title, member_name = "artwork title", "member title"
    task: AsyncResult = dev_download_artworks_by_id.delay(request.model_dump())
    return JSONResponse({
        "task_id": task.id,
        'artwork_id': artwork_id,
        "artwork_title": artwork_title,
        "member_name": member_name,
    })


@router.get("/task/{task_id}")
async def dev_task_status(task_id: str) -> Response:
    """
    (test) Return dev worker task attempt history and terminal status.
    """
    state = get_dev_task_state(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Dev task state not found: {task_id}")
    return JSONResponse(state)


@router.post("/priority/{label}")
async def dev_queue_priority_probe_task(
    label: str,
    priority: int = Query(default=2, ge=1, le=QUEUE_MAX_PRIORITY + 1),  # +1: allow one example of an over-limit value for clamping tests
    sleep_ms: int = Query(default=1000, ge=0, le=10000),
) -> Response:
    """
    (test) Enqueue a no-op task with explicit broker priority and predictable runtime.
    """
    task: AsyncResult = dev_priority_probe_task.apply_async(
        kwargs={
            "request_dict": {
                "label": label,
                "priority": priority,
                "sleep_ms": sleep_ms,
            },
        },
        priority=priority,
    )
    return JSONResponse({
        "task_id": task.id,
        "label": label,
        "priority": priority,
        "sleep_ms": sleep_ms,
    })


@router.get("/priority")
async def dev_priority_probe_status() -> Response:
    """
    (test) Return execution ordering state for dev priority probe tasks.
    """
    return JSONResponse(get_priority_probe_state())
