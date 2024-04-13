import logging
from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from PixivServer.service import subscription

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/member")
async def get_subscribed_members() -> Response:
    """
    Get current list of subscriptions. (format: artist ID | artist name)
    """
    subscribed_members_list = subscription.service.get_subscribed_members()
    response = {'subscriptions': subscribed_members_list}
    return JSONResponse(response)

@router.post("/member/{member_id}")
async def add_member_subscription(member_id: str) -> Response:
    """
    Add a artist to subscriptions.
    """
    response = subscription.service.add_member_subscription(member_id)
    message = f'Subscribed to artist: {response.get("member_name")}.'
    response['message'] = message
    return JSONResponse(response)

@router.delete("/member/{member_id}")
async def delete_member_subscription(member_id: str) -> Response:
    """
    Remove an artist from subscriptions.
    """
    response = subscription.service.delete_member_subscription(member_id)
    message = f'Removed subscription for artist: {response.get("member_name")}.'
    response['message'] = message
    return JSONResponse(response)
