import logging

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse

from PixivServer.models.pixiv_worker import DownloadArtworkByIdRequest
from PixivServer.worker.dev import dev_download_artworks_by_id, get_dev_task_state

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
