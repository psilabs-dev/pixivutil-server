# Download API

Authentication:
- Requires `Authorization: Bearer <api-key>` when `PIXIVUTIL_SERVER_API_KEY` is set.
- If `PIXIVUTIL_SERVER_API_KEY` is unset/empty, authentication is disabled.

`POST /api/queue/download/artwork/{artwork_id}`

Queue download of artwork by ID.

`POST /api/queue/download/member/{member_id}`

Queue download of a member's artworks by member ID.

`POST /api/queue/download/tag/{tag}`

Queue download of all artworks with a given tag (tags should be URL encoded).

> Compatibility note: `/api/download/*` endpoints are still available but
> deprecated. Use `/api/queue/download/*` as the canonical path.
