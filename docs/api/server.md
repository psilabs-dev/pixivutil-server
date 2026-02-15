# Server API

Authentication:
- Requires `Authorization: Bearer <api-key>` when `PIXIVUTIL_SERVER_API_KEY` is set.
- If `PIXIVUTIL_SERVER_API_KEY` is unset/empty, authentication is disabled.

`GET /api/server/cookie`

Get the cookie in use.

`PUT /api/server/cookie/{cookie}`

Update the cookie.

`DELETE /api/server/database`

Reset the database.

`DELETE /api/server/downloads`

Delete the downloads folder.
