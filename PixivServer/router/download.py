import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from fastapi import APIRouter, Response, BackgroundTasks
import traceback

from PixivServer.service import pixiv

logger = logging.getLogger(__name__)
router = APIRouter()

executor = ThreadPoolExecutor(max_workers=1)

async def run_in_threadpool(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, func, *args, **kwargs)

@router.post("/api/download/artwork/{artwork_id}")
async def queue_download_artwork_by_id(artwork_id: str, background_tasks: BackgroundTasks) -> Response:
    """
    Download Pixiv image by ID.
    """
    logger.info(f"Downloading Pixiv artwork by image ID: {artwork_id}.")
    if artwork_id is None:
        return Response(
            content="Artwork ID cannot be None.",
            status_code=400,
        )
    if not artwork_id.isdigit():
        return Response(
            content=f"Artwork ID must be integer; is \"{artwork_id}\" instead.",
            status_code=400
        )
    artwork_id = int(artwork_id)
    try:
        background_tasks.add_task(run_in_threadpool, pixiv.service.download_artwork_by_id, artwork_id)
        # pixiv.service.download_artwork_by_id(artwork_id)
        return Response(
            content=f"Queued download Pixiv artwork: {pixiv.service.get_artwork_name(artwork_id)}.",
            status_code=200
        )
    except Exception as e:
        logger.error("An unexpected error occurred: ", traceback.format_exc())
        return Response(
            content="An unexpected error occurred." + traceback.format_exc(),
            status_code=500,
        )

@router.post("/api/download/member/{member_id}")
async def queue_download_artworks_by_member_id(member_id: str, background_tasks: BackgroundTasks) -> Response:
    """
    Download Pixiv image by member ID.
    """
    logger.info(f"Downloading Pixiv artworks by member ID: {member_id}.")
    if member_id is None:
        return Response(
            content="Member ID cannot be None.",
            status_code=400,
        )
    if not member_id.isdigit():
        return Response(
            content=f"Member ID must be an integer; is \"{member_id}\" instead."
        )
    try:
        background_tasks.add_task(run_in_threadpool, pixiv.service.download_artworks_by_member_id, member_id)
        # pixiv.service.download_artworks_by_member_id(member_id)
        return Response(
            content=f"Queued download Pixiv artworks by member: {pixiv.service.get_member_name(member_id)}.",
            status_code=200
        )
    except Exception as e:
        logger.error("An unexpected error occurred: ", traceback.format_exc())
        return Response(
            content="An unexpected error occurred." + traceback.format_exc(),
            status_code=500,
        )
