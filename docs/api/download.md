# Download API

Authentication:
- Requires `Authorization: Bearer <api-key>` when `PIXIVUTIL_SERVER_API_KEY` is set.
- If `PIXIVUTIL_SERVER_API_KEY` is unset/empty, authentication is disabled.

All endpoints here are queue operations: they enqueue a job for the single worker and return immediately with a `task_id`. They do not wait for the download.

## Queue priority

| Endpoint | Default priority |
| --- | --- |
| `POST /api/queue/download/artwork/{artwork_id}` | `3` |
| `POST /api/queue/download/member/{member_id}` | `2` |
| `POST /api/queue/download/tag/{tag}` | `1` |
| `DELETE /api/queue/download/artwork/{artwork_id}` | `2` |

## Endpoints

`POST /api/queue/download/artwork/{artwork_id}`

Queue download of artwork by ID.

`POST /api/queue/download/member/{member_id}`

Queue download of a member's artworks by member ID.

`POST /api/queue/download/tag/{tag}`

Queue download of all artworks with a given tag. The tag is URL-decoded by the server, so it should be URL encoded by the caller and may contain special characters.

> Compatibility note: `/api/download/*` endpoints are still available but deprecated. Use `/api/queue/download/*` as the canonical path.
