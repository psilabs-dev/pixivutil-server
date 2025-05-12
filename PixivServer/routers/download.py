from celery.result import AsyncResult
import logging
from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from PixivServer.service.pixiv import service
from PixivServer.worker import download_artworks_by_id, download_artworks_by_member_id, download_artworks_by_tag

logger = logging.getLogger('uvicorn.pixivutil')
router = APIRouter()

@router.post("/artwork/{artwork_id}")
async def queue_download_artwork_by_id(artwork_id: str) -> Response:
    """
    Download Pixiv image by ID.
    """
    logger.info(f"Downloading Pixiv artwork by image ID: {artwork_id}.")
    artwork_title = service.get_artwork_name(artwork_id)
    task: AsyncResult = download_artworks_by_id.delay(artwork_id)
    return JSONResponse({
        "task_id": task.id,
        'artwork_id': artwork_id,
        "artwork_title": artwork_title,
    })

@router.post("/member/{member_id}")
async def queue_download_artworks_by_member_id(member_id: str) -> Response:
    """
    Download Pixiv image by member ID.
    """
    logger.info(f"Downloading Pixiv artworks by member ID: {member_id}.")
    member_name = service.get_member_name(member_id)
    task: AsyncResult = download_artworks_by_member_id.delay(member_id)
    return JSONResponse({
        "task_id": task.id,
        'member_id': member_id,
        "member_name": member_name,
    })

@router.post("/tag/{tag_name}")
async def queue_download_artworks_by_tag(tag_name: str) -> Response:
    """
    Download Pixiv images that have a given tag.
    """
    logger.info(f"Downloading Pixiv artworks that have the tag: {tag_name}.")
    task: AsyncResult = download_artworks_by_tag.delay(tag_name)
    return JSONResponse({
        'task_id': task.id,
        'tag': tag_name,
    })