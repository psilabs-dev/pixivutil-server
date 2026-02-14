from __future__ import annotations


class PixivClientError(Exception):
    """Base client exception."""


class PixivTransportError(PixivClientError):
    """Network/transport-level error."""


class PixivAPIError(PixivClientError):
    """API-level error response."""

    def __init__(self, status: int, message: str, body: object | None = None) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.message = message
        self.body = body
