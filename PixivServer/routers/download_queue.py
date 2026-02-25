import datetime
import logging
import sqlite3
import urllib.parse
from datetime import timedelta

from celery.result import AsyncResult
from fastapi import APIRouter, Query, Response
from fastapi.responses import JSONResponse
from pixivutil_server_common.models import TagSortOrder, TagTypeMode

from PixivServer.config.celery import QUEUE_MAX_PRIORITY
from PixivServer.models.pixiv_worker import (
    DeleteArtworkByIdRequest,
    DownloadArtworkByIdRequest,
    DownloadArtworksByMemberIdRequest,
    DownloadArtworksByTagsRequest,
)
from PixivServer.repository.pixivutil import PixivUtilRepository
from PixivServer.utils import is_valid_date
from PixivServer.worker.download import (
    delete_artwork_by_id,
    download_artworks_by_id,
    download_artworks_by_member_id,
    download_artworks_by_tag,
)

logger = logging.getLogger('uvicorn.pixivutil')
router = APIRouter()

def get_artwork_and_member_name_from_db(artwork_id: int) -> tuple[str | None, str | None]:
    repository = PixivUtilRepository()
    try:
        repository.open()
        image_data = repository.get_image_data_by_id(artwork_id)
        return image_data.image.title, image_data.member.name
    except KeyError:
        return None, None
    except sqlite3.Error as e:
        logger.error(f"Database error while getting artwork metadata for {artwork_id}: {e}")
        return None, None
    finally:
        repository.close()


def get_member_name_from_db(member_id: int) -> str | None:
    repository = PixivUtilRepository()
    try:
        repository.open()
        member_data = repository.get_member_data_by_id(member_id)
        return member_data.member.name
    except KeyError:
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error while getting member metadata for {member_id}: {e}")
        return None
    finally:
        repository.close()


@router.post("/artwork/{artwork_id}")
async def queue_download_artwork_by_id(
    artwork_id: str,
    priority: int = Query(default=QUEUE_MAX_PRIORITY, ge=1, le=QUEUE_MAX_PRIORITY),
) -> Response:
    """
    Download Pixiv image by ID.
    """
    logger.info(f"Downloading Pixiv artwork by image ID: {artwork_id}.")
    request = DownloadArtworkByIdRequest(artwork_id=int(artwork_id))
    artwork_title, member_name = get_artwork_and_member_name_from_db(request.artwork_id)
    task: AsyncResult = download_artworks_by_id.apply_async(args=[request.model_dump()], priority=priority)
    return JSONResponse({
        "task_id": task.id,
        'artwork_id': artwork_id,
        "artwork_title": artwork_title,
        "member_name": member_name,
    })

@router.post("/member/{member_id}")
async def queue_download_artworks_by_member_id(
    member_id: str,
    priority: int = Query(default=2, ge=1, le=QUEUE_MAX_PRIORITY),
) -> Response:
    """
    Download Pixiv image by member ID.
    """
    logger.info(f"Downloading Pixiv artworks by member ID: {member_id}.")
    request = DownloadArtworksByMemberIdRequest(member_id=int(member_id))
    member_name = get_member_name_from_db(request.member_id)
    task: AsyncResult = download_artworks_by_member_id.apply_async(args=[request.model_dump()], priority=priority)
    return JSONResponse({
        "task_id": task.id,
        'member_id': member_id,
        "member_name": member_name,
    })

@router.post("/tag/{tag_name}")
async def queue_download_artworks_by_tag(
    tag_name: str,
    bookmark_count: int | None = None,
    sort_order: TagSortOrder = 'date_d',
    type_mode: TagTypeMode = 'a',
    wildcard: bool = False,
    start_date: str | None = None,
    end_date: str | None = None,
    lookback_days: int | None = None,
    priority: int = Query(default=1, ge=1, le=QUEUE_MAX_PRIORITY),
) -> Response:
    """
    Download Pixiv images that have a given tag.
    The tag_name is automatically URL-decoded and can contain special characters.
    Recommendation when calling this API is to set a limit on bookmark count and start date,
    to avoid downloading too many images (e.g. bookmark_count = 100, start_date = 1 month ago).

    start_date: Optional[str] format: YYYY-MM-DD
    end_date: Optional[str] format: YYYY-MM-DD
    lookback_days: Optional[int]: get all artworks between now and lookback_days ago

    If both start_date and lookback_days are provided, the start_date will be ignored.
    """
    if start_date and not is_valid_date(start_date):
        return JSONResponse({
            "error": "Invalid start_date format. Expected format: YYYY-MM-DD"
        }, status_code=400)
    if end_date and not is_valid_date(end_date):
        return JSONResponse({
            "error": "Invalid end_date format. Expected format: YYYY-MM-DD"
        }, status_code=400)

    if lookback_days:
        start_date = (datetime.datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

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
    task: AsyncResult = download_artworks_by_tag.apply_async(args=[request.model_dump()], priority=priority)
    return JSONResponse({
        'task_id': task.id,
        'tag': decoded_tag,
    })

@router.delete("/artwork/{artwork_id}")
async def queue_delete_artwork_by_id(
    artwork_id: str,
    delete_metadata: bool = True,
    priority: int = Query(default=2, ge=1, le=QUEUE_MAX_PRIORITY),
) -> Response:
    """
    Delete Pixiv image by ID from database and filesystem.

    Args:
        artwork_id: The Pixiv artwork ID to delete
        delete_metadata: If True (default), also deletes metadata (date_info, ai_info, series).
                        If False, only deletes artwork files and basic records.

    This is a queue operation as it operates on a sqlite database.
    """
    logger.info(f"Deleting Pixiv artwork by image ID: {artwork_id} (delete_metadata={delete_metadata}).")
    request = DeleteArtworkByIdRequest(artwork_id=int(artwork_id), delete_metadata=delete_metadata)
    task: AsyncResult = delete_artwork_by_id.apply_async(args=[request.model_dump()], priority=priority)
    return JSONResponse({
        "task_id": task.id,
        'artwork_id': artwork_id,
        'delete_metadata': delete_metadata,
    })
