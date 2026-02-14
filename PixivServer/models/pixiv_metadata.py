"""
Model layer for PixivUtil server API interface.

Used to handle metadata GET requests by PixivUtil server API clients for the PixivUtil2 database.
"""

from typing import Optional
from pydantic import BaseModel, Field

class PixivMasterMember(BaseModel):
    """
    pixiv_master_member
    """
    member_id: int
    name: str
    save_folder: str
    created_date: str
    last_update_date: str
    last_image: int
    is_deleted: int
    member_token: Optional[str] = Field(None)

class PixivMasterImage(BaseModel):
    """
    pixiv_master_image
    """
    image_id: int
    member_id: int
    title: str
    save_name: str
    created_date: str
    last_update_date: str
    is_manga: str
    caption: Optional[str]

class PixivMangaImage(BaseModel):
    """
    pixiv_manga_image
    """
    image_id: int
    page: int
    save_name: str
    created_date: str
    last_update_date: str

class PixivMasterTag(BaseModel):
    """
    pixiv_master_tag
    """
    tag_id: str
    created_date: str
    last_update_date: str

class PixivDateInfo(BaseModel):
    """
    pixiv_date_info
    """
    image_id: int
    created_date_epoch: int
    uploaded_date_epoch: int
    created_date: str
    last_update_date: str

class PixivTagTranslation(BaseModel):
    """
    pixiv_tag_translation
    """
    tag_id: str
    translation_type: str
    translation: str
    created_date: str
    last_update_date: str

class PixivImageToTag(BaseModel):
    """
    pixiv_image_to_tag
    """
    image_id: int
    tag_id: str
    created_date: str
    last_update_date: str

class PixivMasterSeries(BaseModel):
    """
    pixiv_master_series
    """
    series_id: str
    series_title: str
    series_type: str
    series_description: Optional[str] = Field(None)
    created_date: str
    last_update_date: str

class PixivImageToSeries(BaseModel):
    """
    pixiv_image_to_series
    """
    series_id: str
    series_order: int
    image_id: int
    created_date: str
    last_update_date: str

# Composite data structures

class PixivMemberPortfolio(BaseModel):
    """
    member + images under member
    """
    member: PixivMasterMember
    images: list[PixivMasterImage]

class PixivImageComplete(BaseModel):
    """
    Complete image data
    """
    image: PixivMasterImage
    member: PixivMasterMember
    pages: list[PixivMangaImage]
    series: Optional[tuple[PixivImageToSeries, PixivMasterSeries]] = Field(None, description="Optional series info from an artwork, if available.")
    tags: list[tuple[PixivImageToTag, PixivMasterTag, Optional[PixivTagTranslation]]]
    dates: Optional[PixivDateInfo] = Field(None, description="Optional created/uploaded date info for artwork.")

class PixivTagInfo(BaseModel):
    """
    Tag info and images with tag
    """
    tag: PixivMasterTag
    translations: list[PixivTagTranslation]
    images: list[PixivImageToTag]

class PixivSeriesInfo(BaseModel):
    """
    Series info and images with series
    """
    series: PixivMasterSeries
    images: list[PixivImageToSeries]
