# Metadata API

Authentication:
- Requires `Authorization: Bearer <api-key>` when `PIXIVUTIL_SERVER_API_KEY` is set.
- If `PIXIVUTIL_SERVER_API_KEY` is unset/empty, authentication is disabled.

All endpoints here are queue operations: they enqueue a job for the single worker and return immediately with a `task_id`. They do not wait for the metadata fetch.

## Queue priority

| Endpoint | Default priority |
| --- | --- |
| `POST /api/queue/metadata/artwork/{artwork_id}` | `2` |
| `POST /api/queue/metadata/member/{member_id}` | `2` |
| `POST /api/queue/metadata/series/{series_id}` | `1` |
| `POST /api/queue/metadata/tag/{tag}` | `1` |

## Endpoints

`POST /api/queue/metadata/artwork/{artwork_id}`

Queue download of artwork metadata by ID.

`POST /api/queue/metadata/member/{member_id}`

Queue download of member metadata by ID.

`POST /api/queue/metadata/series/{series_id}`

Queue download of series metadata by ID.

`POST /api/queue/metadata/tag/{tag}`

Queue download of tag metadata by tag name. The tag is URL-decoded by the server, so it should be URL encoded by the caller. Optional query: `filter_mode` in `none`, `pixpedia`, `translation`, `pixpedia_or_translation`.

> Breaking change: `/api/metadata/*` endpoints were removed. Use `/api/queue/metadata/*` instead.
