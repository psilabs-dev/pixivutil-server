import logging
from typing import Optional
from fastapi import APIRouter, Response
from fastapi.encoders import jsonable_encoder
import json
import traceback

from PixivServer.service import pixiv

logger = logging.getLogger('uvicorn.pixivutil')
router = APIRouter()

@router.get("/member/{member_id}")
async def download_member_info_by_id(member_id: Optional[str]):
    logger.info(f"Retrieving member info by ID: {member_id}.")
    if member_id is None:
        return Response(
            content="Member ID cannot be None.",
            status_code=400,
        )
    if not member_id.isdigit():
        return Response(
            content=f"Member ID must be integer; is \"{member_id}\" instead.",
            status_code=400,
        )
    member_id = int(member_id)
    try:
        member_data, response = pixiv.service.get_member_data(member_id)
        member_json = json.dumps(jsonable_encoder(member_data))
        return Response(
            content=member_json,
            status_code=200,
        )
    except Exception:
        logger.error("An unexpected error occurred: ", traceback.format_exc())
        return Response(
            content="An unexpected error occurred." + traceback.format_exc(),
            status_code=500,
        )

@router.get("/artwork/{artwork_id}")
async def download_artwork_info_by_id(artwork_id: Optional[str]):
    logger.info(f"Retrieving artwork info by ID: {artwork_id}.")
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
        image_data, _ = pixiv.service.get_artwork_data(artwork_id)
        image_json = json.dumps(jsonable_encoder(image_data))

        return Response(
            content=image_json,
            status_code=200
        )
    except Exception:
        logger.error("An unexpected error occurred: ", traceback.format_exc())
        return Response(
            content="An unexpected error occurred." + traceback.format_exc(),
            status_code=500,
        )