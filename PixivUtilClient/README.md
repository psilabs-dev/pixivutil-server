# pixivutil-server-client

Async `aiohttp` client SDK for PixivUtil Server.

## Example

```python
import asyncio

from pixivutil_client import PixivAsyncClient


async def main() -> None:
    async with PixivAsyncClient(
        base_url="http://localhost:8000",
        api_key="your-api-key",
    ) as client:
        health = await client.health()
        print(health)

        queued = await client.queue_download_artwork(123456)
        print(queued.task_id)


asyncio.run(main())
```

## Install

From PyPI:

```sh
uv pip install pixivutil-server-client
```

From the `pixivutil-server` project root:

```sh
uv pip install -e ./PixivUtilClient
```

## Test

From the `pixivutil-server` project root:

```sh
uv run --package pixivutil-server-client pytest PixivUtilClient/tests
```
