"""
Model layer for PixivUtil worker queue processing interface.
"""

from typing import Literal, Optional
from pydantic import BaseModel


class DownloadArtworkByIdRequest(BaseModel):
    artwork_id: int

class DownloadArtworksByMemberIdRequest(BaseModel):
    member_id: int

class DownloadArtworksByTagsRequest(BaseModel):
    """
    See menu_download_by_tags in PixivUtil2.py for more details.
    """
    tags: str
    wildcard: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    bookmark_count: Optional[int] = None
    sort_order: Literal[
        'date_d', 'date', 'popular_d', 'popular_male_d', 'popular_female_d',
    ]
    type_mode: Literal['a', 'i', 'm'] = 'a'

class DeleteArtworkByIdRequest(BaseModel):
    artwork_id: int
    delete_metadata: bool = True


class DownloadMemberMetadataByIdRequest(BaseModel):
    member_id: int


class DownloadArtworkMetadataByIdRequest(BaseModel):
    artwork_id: int


class DownloadSeriesMetadataByIdRequest(BaseModel):
    series_id: int


class DownloadTagMetadataByIdRequest(BaseModel):
    tag: str
    filter_mode: Literal[
        "none", "pixpedia", "translation", "pixpedia_or_translation"
    ] = "none"
