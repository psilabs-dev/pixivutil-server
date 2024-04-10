# Installation

Before installing, prepare the `PixivUtil2` git submodule.
```sh
git submodule init && git submodule update
```
This will clone the `PixivUtil2` repository.

## PixivUtil Web Server

### Install with Docker
Build the Docker image.
```sh
docker build -t pixivutil-server -f docker/Dockerfile .
```
Run bare web server (make the directories `.pixivUtil2` and `downloads` *before* starting container)
```sh
docker run -it --rm -p 8000:8000 \
    -v ./.pixivUtil2:/workdir/.pixivUtil2 \
    -v ./downloads:/workdir/downloads \
    -e PIXIVUTIL_COOKIE=$PIXIVUTIL_COOKIE \
    --name pixivutil-server \
    pixivutil-server
```
### Basic Matrix Notifications Support
If using Matrix notifications, run with additional environment variables.  (can remove `REQUESTS_CA_BUNDLE` if not using self-signed CA at `/usr/local/share/ca-certificates/ca.crt`)
```sh
docker run -it --rm -p 8000:8000 \
    -v ./.pixivUtil2:/workdir/.pixivUtil2 \
    -v ./downloads:/workdir/downloads \
    -v /usr/local/share/ca-certificates:/usr/local/share/ca-certificates \
    -e PIXIVUTIL_COOKIE=$PIXIVUTIL_COOKIE \
    -e REQUESTS_CA_BUNDLE=$REQUESTS_CA_BUNDLE \
    -e MATRIX_HOST=$MATRIX_HOST \
    -e MATRIX_ACCESS_TOKEN=$MATRIX_ACCESS_TOKEN \
    -e MATRIX_ROOM=$MATRIX_ROOM \
    --name pixivutil-server \
    pixivutil-server
```

### Install from Source
Install dependencies.
```sh
pip install -r requirements.txt
pip install -r PixivUtil2/requirements.txt
```
Run the web server.
```sh
uvicorn PixivServer.app:app --host 0.0.0.0 --port 8000
```

### Post Installation
Verify the server is running:
```sh
curl localhost:8000/api/health
```

### API Reference

- [download](/docs/api/download.md)