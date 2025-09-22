import logging
from fastapi import APIRouter, Response


try:
    import lanraragi
except ModuleNotFoundError:
    lanraragi = None

logger = logging.getLogger('uvicorn.pixivutil')
router = APIRouter()

@router.get("/health")
async def is_lrr_configured() -> Response:
    """
    Returns whether LRR is configured (and if aio-lanraragi is installed).
    """
    if lanraragi is None:
        return Response(
            content="aio-lanraragi is not installed.",
            status_code=500
        )
    return Response(
        content="aio-lanraragi is installed.",
        status_code=200
    )
