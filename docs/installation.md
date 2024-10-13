# Installation

Before installing, prepare the `PixivUtil2` git submodule.
```sh
git submodule init && git submodule update
```
This will clone the `PixivUtil2` repository.

## PixivUtil Web Server

### Install with Docker
Build and run with Docker compose. A pixiv cookie is required at `PIXIVUTIL_COOKIE`.
```sh
docker compose up --build
```
Make a request to download an artwork:
```sh
curl -X POST http://localhost:8000/api/download/artwork/{artwork-id-here}
```

### API Reference

- [download](/docs/api/download.md)