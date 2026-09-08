# Health API

Authentication:
- `GET /api/health/` is always public and never requires an API key. Use for container healthcheck.
- `GET /api/health/pixiv` requires `Authorization: Bearer <api-key>` when `PIXIVUTIL_SERVER_API_KEY` is set.

`GET /api/health/`

Check if the server is running. Returns `success`.

`GET /api/health/pixiv`

Check if the Pixiv cookie is effective.

Responses:
- `200`: `Pixiv login works!`
- `403`: `Pixiv login failed.` (cookie is missing, expired, or rejected)
- `401`: API key missing or invalid (only when authentication is enabled)
