# Server API

Authentication:
- Requires `Authorization: Bearer <api-key>` when `PIXIVUTIL_SERVER_API_KEY` is set.
- If `PIXIVUTIL_SERVER_API_KEY` is unset/empty, authentication is disabled.

`GET /api/server/cookie`

Get the cookie in use.

`PUT /api/server/cookie`

Update the cookie. The cookie is sent in the JSON request body, so it does not end up in URLs or access logs.

```json
{"cookie": "<your-pixiv-cookie>"}
```

`DELETE /api/server/database`

Reset the database.

`DELETE /api/server/downloads`

Delete the downloads folder.

> Compatibility note: `PUT /api/server/cookie/{cookie}` is still available but deprecated. Use `PUT /api/server/cookie` with a request body instead.
