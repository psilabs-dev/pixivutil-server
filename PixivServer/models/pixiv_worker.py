"""
Model layer for PixivUtil worker queue processing interface.
"""

from pydantic import BaseModel
from pixivutil_server_common.models import TagMetadataFilterMode, TagSortOrder, TagTypeMode


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
    start_date: str | None = None
    end_date: str | None = None
    bookmark_count: int | None = None
    sort_order: TagSortOrder
    type_mode: TagTypeMode = 'a'

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
    filter_mode: TagMetadataFilterMode = "none"
