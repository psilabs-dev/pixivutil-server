import json
from typing import Any

import pytest
import pytest_asyncio
from aiohttp import web

from pixivutil_client import PixivAPIError, PixivAsyncClient


@pytest_asyncio.fixture
async def server_url() -> str:
    app = web.Application()

    async def plain_json(_: web.Request) -> web.Response:
        return web.Response(text=json.dumps([1, 2, 3]), content_type="text/plain")

    async def auth_echo(request: web.Request) -> web.Response:
        return web.json_response({"authorization": request.headers.get("Authorization")})

    async def failure(_: web.Request) -> web.Response:
        return web.json_response({"error": "bad request"}, status=400)

    app.router.add_get("/api/database/members", plain_json)
    app.router.add_post("/api/queue/download/artwork/123", auth_echo)
    app.router.add_get("/boom", failure)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()

    sockets = site._server.sockets  # type: ignore[attr-defined]
    port = sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}"

    await runner.cleanup()


@pytest.mark.asyncio
async def test_parse_text_json_payload(server_url: str) -> None:
    async with PixivAsyncClient(server_url) as client:
        members = await client.get_member_ids()
        assert members == [1, 2, 3]


@pytest.mark.asyncio
async def test_send_authorization_header(server_url: str) -> None:
    async with PixivAsyncClient(server_url, api_key="abc123") as client:
        response = await client._request("POST", "/api/queue/download/artwork/123")
        assert response["authorization"] == "Bearer abc123"


@pytest.mark.asyncio
async def test_raise_api_error(server_url: str) -> None:
    async with PixivAsyncClient(server_url) as client:
        with pytest.raises(PixivAPIError) as exc:
            await client._request("GET", "/boom")
        assert exc.value.status == 400
        assert exc.value.message == "bad request"


@pytest.mark.asyncio
async def test_ssl_flag_is_forwarded() -> None:
    captured: dict[str, Any] = {}

    class FakeResponse:
        status = 200

        async def text(self) -> str:
            return json.dumps({"ok": True})

    class FakeContextManager:
        def __init__(self, response: FakeResponse):
            self._response = response

        async def __aenter__(self) -> FakeResponse:
            return self._response

        async def __aexit__(self, *_: object) -> None:
            return None

    class FakeSession:
        closed = False

        def request(self, method: str, url: str, **kwargs: Any) -> FakeContextManager:
            captured["method"] = method
            captured["url"] = url
            captured["kwargs"] = kwargs
            return FakeContextManager(FakeResponse())

    client = PixivAsyncClient("https://example.invalid", ssl=False, session=FakeSession())  # type: ignore[arg-type]
    payload = await client._request("GET", "/probe")
    assert payload["ok"] is True
    assert captured["kwargs"]["ssl"] is False
