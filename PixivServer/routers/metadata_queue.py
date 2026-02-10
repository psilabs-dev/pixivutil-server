import logging
from typing import Literal, Optional

from celery.result import AsyncResult
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from PixivServer.models.pixiv_worker import (
    DownloadArtworkMetadataByIdRequest,
    DownloadMemberMetadataByIdRequest,
    DownloadSeriesMetadataByIdRequest,
    DownloadTagMetadataByIdRequest,
)
from PixivServer.worker import (
    download_artwork_metadata_by_id,
    download_member_metadata_by_id,
    download_series_metadata_by_id,
    download_tag_metadata_by_id,
)

logger = logging.getLogger("uvicorn.pixivutil")
router = APIRouter()


@router.post("/member/{member_id}")
async def queue_download_member_metadata_by_id(member_id: str) -> JSONResponse:
    """
    Queue download of member metadata by ID.
    """
    if not member_id.isdigit():
        return JSONResponse(
            {"error": f'Member ID must be integer; is "{member_id}" instead.'},
            status_code=400,
        )
    member_id_int = int(member_id)
    logger.info(f"Queueing member metadata download by ID: {member_id_int}.")
    request = DownloadMemberMetadataByIdRequest(member_id=member_id_int)
    task: AsyncResult = download_member_metadata_by_id.delay(request.model_dump())
    return JSONResponse({"task_id": task.id, "member_id": member_id_int})


@router.post("/artwork/{artwork_id}")
async def queue_download_artwork_metadata_by_id(artwork_id: str) -> JSONResponse:
    """
    Queue download of artwork metadata by ID.
    """
    if not artwork_id.isdigit():
        return JSONResponse(
            {"error": f'Artwork ID must be integer; is "{artwork_id}" instead.'},
            status_code=400,
        )
    artwork_id_int = int(artwork_id)
    logger.info(f"Queueing artwork metadata download by ID: {artwork_id_int}.")
    request = DownloadArtworkMetadataByIdRequest(artwork_id=artwork_id_int)
    task: AsyncResult = download_artwork_metadata_by_id.delay(request.model_dump())
    return JSONResponse({"task_id": task.id, "artwork_id": artwork_id_int})


@router.post("/series/{series_id}")
async def queue_download_series_metadata_by_id(series_id: str) -> JSONResponse:
    """
    Queue download of series metadata by ID.
    """
    if not series_id.isdigit():
        return JSONResponse(
            {"error": f'Series ID must be integer; is "{series_id}" instead.'},
            status_code=400,
        )
    series_id_int = int(series_id)
    logger.info(f"Queueing series metadata download by ID: {series_id_int}.")
    request = DownloadSeriesMetadataByIdRequest(series_id=series_id_int)
    task: AsyncResult = download_series_metadata_by_id.delay(request.model_dump())
    return JSONResponse({"task_id": task.id, "series_id": series_id_int})


@router.post("/tag/{tag}")
async def queue_download_tag_metadata_by_id(
    tag: str,
    filter_mode: Optional[
        Literal["none", "pixpedia", "translation", "pixpedia_or_translation"]
    ] = "none",
) -> JSONResponse:
    """
    Queue download of tag metadata by tag ID/name.
    """
    logger.info(f"Queueing tag metadata download: {tag} (filter_mode={filter_mode}).")
    request = DownloadTagMetadataByIdRequest(tag=tag, filter_mode=filter_mode or "none")
    task: AsyncResult = download_tag_metadata_by_id.delay(request.model_dump())
    return JSONResponse(
        {"task_id": task.id, "tag": tag, "filter_mode": request.filter_mode}
    )
