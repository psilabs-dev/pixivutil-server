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
docker build -t pixivutil2-server -f docker/Dockerfile .
```
Run the container (if self-signed certificate is in `/usr/local/share/ca-certificates/ca.crt`)
```sh
docker run -it --rm -p 8000:8000 \
    -v ./.pixivUtil2:/workdir/.pixivUtil2 \
    -v /usr/local/share/ca-certificates:/usr/local/share/ca-certificates \
    -e REQUESTS_CA_BUNDLE=$REQUESTS_CA_BUNDLE \
    -e MATRIX_HOST=$MATRIX_HOST \
    -e MATRIX_ACCESS_TOKEN=$MATRIX_ACCESS_TOKEN \
    -e MATRIX_ROOM=$MATRIX_ROOM \
    pixivutil2-server
```

### Install from Source
Install dependencies.
```sh
pip install -r requirements.txt
pip install -r PixivUtil2/requirements/web.txt
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
