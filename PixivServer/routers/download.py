from typing import Literal, Optional
from celery.result import AsyncResult
import logging
from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
import urllib.parse

from PixivServer.service.pixiv import service
from PixivServer.worker import download_artworks_by_id, download_artworks_by_member_id, download_artworks_by_tag
from PixivServer.models.pixiv import DownloadArtworkByIdRequest, DownloadArtworksByMemberIdRequest, DownloadArtworksByTagsRequest
from PixivServer.utils import is_valid_date

logger = logging.getLogger('uvicorn.pixivutil')
router = APIRouter()

@router.post("/artwork/{artwork_id}")
async def queue_download_artwork_by_id(artwork_id: str) -> Response:
    """
    Download Pixiv image by ID.
    """
    logger.info(f"Downloading Pixiv artwork by image ID: {artwork_id}.")
    request = DownloadArtworkByIdRequest(artwork_id=int(artwork_id))
    artwork_title = service.get_artwork_name(request.artwork_id)
    task: AsyncResult = download_artworks_by_id.delay(request.model_dump())
    return JSONResponse({
        "task_id": task.id,
        'artwork_id': artwork_id,
        "artwork_title": artwork_title,
    })

@router.post("/member/{member_id}")
async def queue_download_artworks_by_member_id(member_id: str, include_sketch: bool = False) -> Response:
    """
    Download Pixiv image by member ID.
    """
    logger.info(f"Downloading Pixiv artworks by member ID: {member_id}.")
    request = DownloadArtworksByMemberIdRequest(member_id=int(member_id), include_sketch=include_sketch)
    member_name = service.get_member_name(request.member_id)
    task: AsyncResult = download_artworks_by_member_id.delay(request.model_dump())
    return JSONResponse({
        "task_id": task.id,
        'member_id': member_id,
        "member_name": member_name,
    })

@router.post("/tag/{tag_name}")
async def queue_download_artworks_by_tag(
    tag_name: str, 
    bookmark_count: int = 0, 
    sort_order: Literal['date_d', 'date', 'popular_d', 'popular_male_d', 'popular_female_d'] = 'date_d', 
    type_mode: Literal['a', 'i', 'm'] = 'a',
    wildcard: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Response:
    """
    Download Pixiv images that have a given tag.
    The tag_name is automatically URL-decoded and can contain special characters.
    Recommendation when calling this API is to set a limit on bookmark count and start date,
    to avoid downloading too many images (e.g. bookmark_count = 100, start_date = 1 month ago).

    start_date: Optional[str] format: YYYY-MM-DD
    end_date: Optional[str] format: YYYY-MM-DD
    """
    if start_date and not is_valid_date(start_date):
        return JSONResponse({
            "error": "Invalid start_date format. Expected format: YYYY-MM-DD"
        }, status_code=400)
    if end_date and not is_valid_date(end_date):
        return JSONResponse({
            "error": "Invalid end_date format. Expected format: YYYY-MM-DD"
        }, status_code=400)

    decoded_tag = urllib.parse.unquote(tag_name)
    logger.info(f"Downloading Pixiv artworks that have the tag: {decoded_tag}")
    request = DownloadArtworksByTagsRequest(
        tags=decoded_tag,
        bookmark_count=bookmark_count,
        sort_order=sort_order,
        type_mode=type_mode,
        wildcard=wildcard,
        start_date=start_date,
        end_date=end_date,
    )
    task: AsyncResult = download_artworks_by_tag.delay(request.model_dump())
    return JSONResponse({
        'task_id': task.id,
        'tag': decoded_tag,
    })
