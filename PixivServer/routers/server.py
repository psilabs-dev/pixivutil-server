import logging
from fastapi import APIRouter, Response

from PixivServer.service import pixiv

logger = logging.getLogger('uvicorn.pixivutil')
router = APIRouter()

@router.get("/cookie")
async def get_cookie() -> Response:
    """
    Get current cookie.
    """
    cookie = pixiv.service.get_pixiv_cookie()
    return Response(
        content=cookie,
        status_code=200,
    )

@router.put("/cookie/{cookie}")
async def update_cookie(cookie: str) -> Response:
    """
    Update (and validate) cookie.
    """
    is_success = pixiv.service.update_pixiv_cookie(cookie)
    if not is_success:
        return Response(
            content="Failed to update cookie.",
            status_code=500
        )
    return Response(
        content=cookie,
        status_code=200,
    )

@router.delete("/database")
async def reset_database() -> Response:
    pixiv.service.reset_database()
    return Response(
        content="Reset database.",
        status_code=200,
    )

@router.delete("/downloads")
async def reset_downloads() -> Response:
    pixiv.service.reset_downloads()
    return Response(
        content="Reset downloads.",
        status_code=200,
    )
