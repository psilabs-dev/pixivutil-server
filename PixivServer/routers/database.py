import logging
import sqlite3
from typing import Optional
from fastapi import APIRouter, Response
from fastapi.encoders import jsonable_encoder
import json

from PixivServer.repository.pixivutil import PixivUtilRepository

logger = logging.getLogger('uvicorn.pixivutil')
router = APIRouter()

@router.get("/members")
def get_all_pixiv_member_ids() -> Response:
    """Get all member IDs from the database."""
    logger.info("Getting all member IDs from database.")

    repository = PixivUtilRepository()

    try:
        repository.open()
        member_ids = repository.get_all_pixiv_member_ids()

        member_ids_json = json.dumps(member_ids)
        return Response(
            content=member_ids_json,
            status_code=200,
        )
    except sqlite3.Error as e:
        logger.error(f"Database error while getting all member IDs: {e}")
        return Response(
            content="Database error occurred.",
            status_code=500,
        )
    except Exception as e:
        logger.error(f"Unexpected error while getting all member IDs: {e}")
        return Response(
            content="An unexpected error occurred.",
            status_code=500,
        )
    finally:
        repository.close()

@router.get("/images")
def get_all_pixiv_image_ids() -> Response:
    """Get all image IDs from the database."""
    logger.info("Getting all image IDs from database.")

    repository = PixivUtilRepository()

    try:
        repository.open()
        image_ids = repository.get_all_pixiv_image_ids()

        image_ids_json = json.dumps(image_ids)
        return Response(
            content=image_ids_json,
            status_code=200,
        )
    except sqlite3.Error as e:
        logger.error(f"Database error while getting all image IDs: {e}")
        return Response(
            content="Database error occurred.",
            status_code=500,
        )
    except Exception as e:
        logger.error(f"Unexpected error while getting all image IDs: {e}")
        return Response(
            content="An unexpected error occurred.",
            status_code=500,
        )
    finally:
        repository.close()

@router.get("/tags")
def get_all_pixiv_tags() -> Response:
    """Get all tag IDs from the database."""
    logger.info("Getting all tag IDs from database.")

    repository = PixivUtilRepository()

    try:
        repository.open()
        tag_ids = repository.get_all_pixiv_tags()

        tag_ids_json = json.dumps(tag_ids)
        return Response(
            content=tag_ids_json,
            status_code=200,
        )
    except sqlite3.Error as e:
        logger.error(f"Database error while getting all tag IDs: {e}")
        return Response(
            content="Database error occurred.",
            status_code=500,
        )
    except Exception as e:
        logger.error(f"Unexpected error while getting all tag IDs: {e}")
        return Response(
            content="An unexpected error occurred.",
            status_code=500,
        )
    finally:
        repository.close()

@router.get("/series")
def get_all_pixiv_series() -> Response:
    """Get all series IDs from the database."""
    logger.info("Getting all series IDs from database.")

    repository = PixivUtilRepository()

    try:
        repository.open()
        series_ids = repository.get_all_pixiv_series()

        series_ids_json = json.dumps(series_ids)
        return Response(
            content=series_ids_json,
            status_code=200,
        )
    except sqlite3.Error as e:
        logger.error(f"Database error while getting all series IDs: {e}")
        return Response(
            content="Database error occurred.",
            status_code=500,
        )
    except Exception as e:
        logger.error(f"Unexpected error while getting all series IDs: {e}")
        return Response(
            content="An unexpected error occurred.",
            status_code=500,
        )
    finally:
        repository.close()

@router.get("/member/{member_id}")
def get_pixiv_member_portfolio_by_id(member_id: Optional[str]) -> Response:
    """Get member portfolio data from the database."""
    logger.info(f"Getting member data by ID from database: {member_id}.")

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

    member_id_int = int(member_id)
    repository = PixivUtilRepository()

    try:
        repository.open()
        member_data = repository.get_member_data_by_id(member_id_int)

        member_json = json.dumps(jsonable_encoder(member_data))
        return Response(
            content=member_json,
            status_code=200,
        )
    except KeyError as e:
        logger.info(f"Member not found: {e}")
        return Response(
            content=f"Member with ID {member_id} not found.",
            status_code=404,
        )
    except sqlite3.Error as e:
        logger.error(f"Database error while getting member {member_id}: {e}")
        return Response(
            content="Database error occurred.",
            status_code=500,
        )
    except Exception as e:
        logger.error(f"Unexpected error while getting member {member_id}: {e}")
        return Response(
            content="An unexpected error occurred.",
            status_code=500,
        )
    finally:
        repository.close()

@router.get("/image/{image_id}")
def get_pixiv_image_data_by_id(image_id: Optional[str]) -> Response:
    """Get complete image data from the database."""
    logger.info(f"Getting image data by ID from database: {image_id}.")

    if image_id is None:
        return Response(
            content="Image ID cannot be None.",
            status_code=400,
        )
    if not image_id.isdigit():
        return Response(
            content=f"Image ID must be integer; is \"{image_id}\" instead.",
            status_code=400,
        )

    image_id_int = int(image_id)
    repository = PixivUtilRepository()

    try:
        repository.open()
        image_data = repository.get_image_data_by_id(image_id_int)

        image_json = json.dumps(jsonable_encoder(image_data))
        return Response(
            content=image_json,
            status_code=200,
        )
    except KeyError as e:
        logger.info(f"Image not found: {e}")
        return Response(
            content=f"Image with ID {image_id} not found.",
            status_code=404,
        )
    except sqlite3.Error as e:
        logger.error(f"Database error while getting image {image_id}: {e}")
        return Response(
            content="Database error occurred.",
            status_code=500,
        )
    except Exception as e:
        logger.error(f"Unexpected error while getting image {image_id}: {e}")
        return Response(
            content="An unexpected error occurred.",
            status_code=500,
        )
    finally:
        repository.close()
