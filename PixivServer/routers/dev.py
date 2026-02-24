import logging

from celery.result import AsyncResult
from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from PixivServer.models.pixiv_worker import DownloadArtworkByIdRequest
from PixivServer.worker.dev import dev_download_artworks_by_id

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
