# Installation

Before installing, prepare the `PixivUtil2` git submodule.
```sh
git submodule update --init --recursive
```
This will clone the `PixivUtil2` repository.

## PixivUtil Web Server

### Install with Docker
Build and run with Docker compose. A pixiv cookie is required at `PIXIVUTIL_COOKIE`.
```sh
docker compose up --build
```
This project uses `uv` inside the Docker image to install and run the app.
Make a request to download an artwork:
```sh
curl -X POST http://localhost:8000/api/download/artwork/{artwork-id-here}
```

### API Reference

- [download](/docs/api/download.md)
