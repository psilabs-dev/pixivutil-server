import logging
from fastapi import APIRouter, Depends, Response

import PixivServer.auth
from PixivServer.service import pixiv

logger = logging.getLogger('uvicorn.pixivutil')
router = APIRouter()

@router.get("/")
async def health_check() -> Response:
    logger.info("Received health check API call.")

    return Response(
        content="success",
        status_code=200,
    )

@router.get("/pixiv")
async def pixiv_health_check(
    _: None = Depends(PixivServer.auth.is_valid_api_key_header)
) -> Response:

    cookie = pixiv.service.get_pixiv_cookie()
    pixiv_cookie_is_valid = pixiv.service.login_pixiv(cookie)
    
    if not pixiv_cookie_is_valid:
        return Response(
            content="Pixiv login failed.",
            status_code=403,
        )
    return Response(
        content="Pixiv login works!",
        status_code=200,
    )
