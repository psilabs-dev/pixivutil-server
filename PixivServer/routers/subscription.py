import logging

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from PixivServer.service import subscription

logger = logging.getLogger('uvicorn.pixivutil')
router = APIRouter()

class AddTagSubscriptionRequest(BaseModel):
    tag_id: str
    bookmark_count: int

@router.get("/member")
async def get_subscribed_members() -> Response:
    """
    Get current list of subscriptions. (format: artist ID | artist name)
    """
    subscribed_members_list = subscription.service.get_subscribed_members()
    response = {'subscriptions': subscribed_members_list}
    return JSONResponse(response)

@router.put("/member/{member_id}")
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

@router.get("/tag")
async def get_subscribed_tags() -> Response:
    """
    Get current list of subscriptions.
    """
    subscribed_tags_list = subscription.service.get_subscribed_tags()
    response = {'subscriptions': subscribed_tags_list}
    return JSONResponse(response)

@router.put("/tag")
async def add_tag_subscription(add_tag_subscription_request: AddTagSubscriptionRequest) -> Response:
    """
    Add a tag subscription using json field. Format:

    {
        "tag_id": string
    }
    """
    tag_id = add_tag_subscription_request.tag_id
    bookmark_count = add_tag_subscription_request.bookmark_count
    if len(tag_id) > 255:
        message = f"Tag ID id exceeds 255 characters: {tag_id}"
        response = {
            "message": message
        }
        return JSONResponse(response)
    response = subscription.service.add_tag_subscription(tag_id, bookmark_count)
    print("OK")
    return JSONResponse(response)
