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

    async def dlq_list(_: web.Request) -> web.Response:
        return web.json_response(
            [
                {
                    "dead_letter_id": "abc-123",
                    "task_name": "download_artworks_by_id",
                    "payload": {"artwork_id": 42},
                }
            ]
        )

    async def dlq_resume_all(_: web.Request) -> web.Response:
        return web.json_response({"requeued": 2})

    async def dlq_resume_one(request: web.Request) -> web.Response:
        dead_letter_id = request.match_info["dead_letter_id"]
        return web.json_response(
            {
                "dead_letter_id": dead_letter_id,
                "requeued": True,
                "task_name": "download_artworks_by_id",
            }
        )

    async def dlq_drop_all(_: web.Request) -> web.Response:
        return web.json_response({"dropped": 3})

    async def dlq_drop_one(request: web.Request) -> web.Response:
        dead_letter_id = request.match_info["dead_letter_id"]
        return web.json_response({"dead_letter_id": dead_letter_id, "dropped": True})

    app.router.add_get("/api/database/members", plain_json)
    app.router.add_post("/api/queue/download/artwork/123", auth_echo)
    app.router.add_get("/boom", failure)
    app.router.add_get("/api/queue/dead-letter/", dlq_list)
    app.router.add_post("/api/queue/dead-letter/resume", dlq_resume_all)
    app.router.add_post("/api/queue/dead-letter/{dead_letter_id}/resume", dlq_resume_one)
    app.router.add_delete("/api/queue/dead-letter/", dlq_drop_all)
    app.router.add_delete("/api/queue/dead-letter/{dead_letter_id}", dlq_drop_one)

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


@pytest.mark.asyncio
async def test_dead_letter_queue_client_methods(server_url: str) -> None:
    async with PixivAsyncClient(server_url) as client:
        messages = await client.list_dead_letter_messages()
        assert len(messages) == 1
        assert messages[0].dead_letter_id == "abc-123"
        assert messages[0].payload["artwork_id"] == 42

        resumed_all = await client.resume_all_dead_letter_messages()
        assert resumed_all.requeued == 2

        resumed_one = await client.resume_dead_letter_message("abc-123")
        assert resumed_one.dead_letter_id == "abc-123"
        assert resumed_one.requeued is True

        dropped_all = await client.drop_all_dead_letter_messages()
        assert dropped_all.dropped == 3

        dropped_one = await client.drop_dead_letter_message("abc-123")
        assert dropped_one.dead_letter_id == "abc-123"
        assert dropped_one.dropped is True
