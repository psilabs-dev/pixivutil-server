from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DeadLetterMessage(BaseModel):
    dead_letter_id: str
    task_name: str
    payload: dict


class QueueTaskResponse(BaseModel):
    task_id: str
    artwork_id: str | int | None = None
    member_id: str | int | None = None
    series_id: str | int | None = None
    tag: str | None = None
    filter_mode: str | None = None
    delete_metadata: bool | None = None
    artwork_title: str | None = None
    member_name: str | None = None


class UpdateCookieRequest(BaseModel):
    cookie: str


class PixivMasterMember(BaseModel):
    member_id: int
    name: str
    save_folder: str
    created_date: str
    last_update_date: str
    last_image: int
    is_deleted: int
    member_token: str | None = Field(None)


class PixivMasterImage(BaseModel):
    image_id: int
    member_id: int
    title: str
    save_name: str
    created_date: str
    last_update_date: str
    is_manga: str
    caption: str | None


class PixivMangaImage(BaseModel):
    image_id: int
    page: int
    save_name: str
    created_date: str
    last_update_date: str


class PixivMasterTag(BaseModel):
    tag_id: str
    created_date: str
    last_update_date: str


class PixivDateInfo(BaseModel):
    image_id: int
    created_date_epoch: int
    uploaded_date_epoch: int
    created_date: str
    last_update_date: str


class PixivTagTranslation(BaseModel):
    tag_id: str
    translation_type: str
    translation: str
    created_date: str
    last_update_date: str


class PixivImageToTag(BaseModel):
    image_id: int
    tag_id: str
    created_date: str
    last_update_date: str


class PixivMasterSeries(BaseModel):
    series_id: str
    series_title: str
    series_type: str
    series_description: str | None = Field(None)
    created_date: str
    last_update_date: str


class PixivImageToSeries(BaseModel):
    series_id: str
    series_order: int
    image_id: int
    created_date: str
    last_update_date: str


class PixivMemberPortfolio(BaseModel):
    member: PixivMasterMember
    images: list[PixivMasterImage]


class PixivImageComplete(BaseModel):
    image: PixivMasterImage
    member: PixivMasterMember
    pages: list[PixivMangaImage]
    series: tuple[PixivImageToSeries, PixivMasterSeries] | None = Field(None)
    tags: list[tuple[PixivImageToTag, PixivMasterTag, PixivTagTranslation | None]]
    dates: PixivDateInfo | None = Field(None)


class PixivTagInfo(BaseModel):
    tag: PixivMasterTag
    translations: list[PixivTagTranslation]
    images: list[PixivImageToTag]


class PixivSeriesInfo(BaseModel):
    series: PixivMasterSeries
    images: list[PixivImageToSeries]


# Source-of-truth references in PixivUtil2 (server-mode):
# - TagSortOrder:
#   - PixivUtil2/common/PixivHelper.py::generate_search_tag_url (accepted order tuple)
#   - PixivUtil2/handler/PixivBatchHandler.py::process_job_tags (validation)
#   - PixivUtil2/PixivUtil2.py::menu_download_by_tags (interactive options)
TagSortOrder = Literal["date_d", "date", "popular_d", "popular_male_d", "popular_female_d"]

# - TagTypeMode:
#   - PixivUtil2/PixivUtil2.py::menu_download_by_tags (accepted values a/i/m)
#   - PixivUtil2/handler/PixivBatchHandler.py::process_job_tags (validation)
#   - PixivUtil2/common/PixivHelper.py::generate_search_tag_url (mapping to API values)
TagTypeMode = Literal["a", "i", "m"]

# - TagMetadataFilterMode:
#   - PixivUtil2/PixivUtil2.py::menu_metadata_by_tag (prompt options)
#   - PixivUtil2/handler/PixivTagsHandler.py::process_tag_metadata (filter behavior)
TagMetadataFilterMode = Literal["none", "pixpedia", "translation", "pixpedia_or_translation"]
