


from typing import Literal, Optional
from pydantic import BaseModel


class DownloadArtworkByIdRequest(BaseModel):
    artwork_id: int

class DownloadArtworksByMemberIdRequest(BaseModel):
    member_id: int
    include_sketch: bool = False

class DownloadArtworksByTagsRequest(BaseModel):
    """
    See menu_download_by_tags in PixivUtil2.py for more details.
    """
    tags: str
    wildcard: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    bookmark_count: int = 0
    sort_order: Literal[
        'date_d', 'date', 'popular_d', 'popular_male_d', 'popular_female_d',
    ]
    type_mode: Literal['a', 'i', 'm'] = 'a'
