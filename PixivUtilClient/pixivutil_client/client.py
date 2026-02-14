from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import aiohttp

from pixivutil_client.exceptions import PixivAPIError, PixivTransportError
from pixivutil_client.models import (
    PixivImageComplete,
    PixivMemberPortfolio,
    PixivSeriesInfo,
    PixivTagInfo,
    QueueTaskResponse,
    TagMetadataFilterMode,
    TagSortOrder,
    TagTypeMode,
)


class PixivAsyncClient:
    """Async HTTP client for PixivUtil Server APIs."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout_seconds: float = 30,
        ssl: bool | None = True,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.ssl = ssl
        self._session = session
        self._owns_session = session is None

    async def __aenter__(self) -> "PixivAsyncClient":
        await self._ensure_session()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def close(self) -> None:
        if self._session is not None and self._owns_session:
            await self._session.close()
        self._session = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    def _auth_headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        session = await self._ensure_session()
        url = f"{self.base_url}{path}"

        try:
            async with session.request(
                method,
                url,
                params=params,
                json=json_body,
                headers=self._auth_headers(),
                ssl=self.ssl,
            ) as response:
                payload = await self._decode_payload(response)
                if response.status >= 400:
                    raise PixivAPIError(
                        response.status,
                        self._extract_error_message(payload),
                        body=payload,
                    )
                return payload
        except PixivAPIError:
            raise
        except aiohttp.ClientError as error:
            raise PixivTransportError(str(error)) from error

    async def _decode_payload(self, response: aiohttp.ClientResponse) -> Any:
        raw_text = await response.text()
        if not raw_text:
            return None

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            return raw_text

    def _extract_error_message(self, payload: Any) -> str:
        if isinstance(payload, dict):
            if "detail" in payload:
                return str(payload["detail"])
            if "error" in payload:
                return str(payload["error"])
            if "message" in payload:
                return str(payload["message"])
        if isinstance(payload, str):
            return payload
        return "Request failed"

    async def health(self) -> str:
        payload = await self._request("GET", "/api/health/")
        return str(payload)

    async def health_pixiv(self) -> str:
        payload = await self._request("GET", "/api/health/pixiv")
        return str(payload)

    async def queue_download_artwork(self, artwork_id: int) -> QueueTaskResponse:
        payload = await self._request("POST", f"/api/queue/download/artwork/{artwork_id}")
        return QueueTaskResponse.model_validate(payload)

    async def queue_download_member(self, member_id: int) -> QueueTaskResponse:
        payload = await self._request("POST", f"/api/queue/download/member/{member_id}")
        return QueueTaskResponse.model_validate(payload)

    async def queue_download_tag(
        self,
        tag: str,
        *,
        bookmark_count: int | None = None,
        sort_order: TagSortOrder = "date_d",
        type_mode: TagTypeMode = "a",
        wildcard: bool = False,
        start_date: str | None = None,
        end_date: str | None = None,
        lookback_days: int | None = None,
    ) -> QueueTaskResponse:
        params: dict[str, Any] = {
            "sort_order": sort_order,
            "type_mode": type_mode,
            "wildcard": wildcard,
        }
        if bookmark_count is not None:
            params["bookmark_count"] = bookmark_count
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date
        if lookback_days is not None:
            params["lookback_days"] = lookback_days

        encoded_tag = quote(tag, safe="")
        payload = await self._request("POST", f"/api/queue/download/tag/{encoded_tag}", params=params)
        return QueueTaskResponse.model_validate(payload)

    async def queue_delete_artwork(self, artwork_id: int, delete_metadata: bool = True) -> QueueTaskResponse:
        payload = await self._request(
            "DELETE",
            f"/api/queue/download/artwork/{artwork_id}",
            params={"delete_metadata": str(delete_metadata).lower()},
        )
        return QueueTaskResponse.model_validate(payload)

    async def queue_metadata_artwork(self, artwork_id: int) -> QueueTaskResponse:
        payload = await self._request("POST", f"/api/queue/metadata/artwork/{artwork_id}")
        return QueueTaskResponse.model_validate(payload)

    async def queue_metadata_member(self, member_id: int) -> QueueTaskResponse:
        payload = await self._request("POST", f"/api/queue/metadata/member/{member_id}")
        return QueueTaskResponse.model_validate(payload)

    async def queue_metadata_series(self, series_id: int) -> QueueTaskResponse:
        payload = await self._request("POST", f"/api/queue/metadata/series/{series_id}")
        return QueueTaskResponse.model_validate(payload)

    async def queue_metadata_tag(
        self,
        tag: str,
        filter_mode: TagMetadataFilterMode = "none",
    ) -> QueueTaskResponse:
        encoded_tag = quote(tag, safe="")
        payload = await self._request(
            "POST",
            f"/api/queue/metadata/tag/{encoded_tag}",
            params={"filter_mode": filter_mode},
        )
        return QueueTaskResponse.model_validate(payload)

    async def get_member_ids(self) -> list[int]:
        payload = await self._request("GET", "/api/database/members")
        return list(payload)

    async def get_image_ids(self) -> list[int]:
        payload = await self._request("GET", "/api/database/images")
        return list(payload)

    async def get_tags(self) -> list[str]:
        payload = await self._request("GET", "/api/database/tags")
        return list(payload)

    async def get_series(self) -> list[str]:
        payload = await self._request("GET", "/api/database/series")
        return list(payload)

    async def get_member(self, member_id: int) -> PixivMemberPortfolio:
        payload = await self._request("GET", f"/api/database/member/{member_id}")
        return PixivMemberPortfolio.model_validate(payload)

    async def get_image(self, image_id: int) -> PixivImageComplete:
        payload = await self._request("GET", f"/api/database/image/{image_id}")
        return PixivImageComplete.model_validate(payload)

    async def get_tag(self, tag_id: str) -> PixivTagInfo:
        encoded_tag_id = quote(tag_id, safe="")
        payload = await self._request("GET", f"/api/database/tag/{encoded_tag_id}")
        return PixivTagInfo.model_validate(payload)

    async def get_series_info(self, series_id: str) -> PixivSeriesInfo:
        encoded_series_id = quote(series_id, safe="")
        payload = await self._request("GET", f"/api/database/series/{encoded_series_id}")
        return PixivSeriesInfo.model_validate(payload)

    async def get_cookie(self) -> str:
        payload = await self._request("GET", "/api/server/cookie")
        return str(payload)

    async def update_cookie(self, cookie: str) -> str:
        encoded_cookie = quote(cookie, safe="")
        payload = await self._request("PUT", f"/api/server/cookie/{encoded_cookie}")
        return str(payload)

    async def reset_database(self) -> str:
        payload = await self._request("DELETE", "/api/server/database")
        return str(payload)

    async def reset_downloads(self) -> str:
        payload = await self._request("DELETE", "/api/server/downloads")
        return str(payload)
