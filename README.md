# PixivUtil Server

PixivUtil server is a self-hosted, containerized server solution which provides [PixivUtil2](https://github.com/Nandaka/PixivUtil2) content download operations through an HTTP API interface.

The following key operations are supported through PixivUtil server's API:

- Download artworks by member ID
- Download artwork by image ID
- Download artworks by tag

In addition, server API supports reading of metadata:

- Get image metadata by ID
- Get member metadata by ID
- Get tag metadata by ID
- Get series metadata by ID

The scope of PixivUtil server covers only key Pixiv-related operations within a `uv` environment or Docker cluster. Non-Pixiv APIs, such as Fantia or Fanbox, are not supported, as they cannot be reliably tested.

## Installation

Before installing, prepare the `PixivUtil2` git submodule:
```sh
git submodule update --init --recursive
```
This will clone the `PixivUtil2` repository.

### Deployment

Build and run with Docker compose. A pixiv cookie is required at `PIXIVUTIL_COOKIE`.

```sh
docker compose up --build --remove-orphans
```

This project uses `uv` inside the Docker image to install and run the app.
Make a request to download an artwork:

```sh
curl -X POST http://localhost:8000/api/download/artwork/{artwork-id-here}
```

### API Reference

- [download](/docs/api/download.md)

## Configuration

PixivUtil server applies a downstream server flavor of PixivUtil2 called "Server Mode" [PixivUtil2](https://github.com/psilabs-dev/PixivUtil2). Server Mode applies additional configuration changes to ensure that downloaded Pixiv data is more reliable and available. See the server mode README [here](https://github.com/psilabs-dev/PixivUtil2/blob/server-mode/main/SERVER_README.md).

For further configuration, apply them at `.pixivUtil2/conf/conf.ini` (refer to [Pixivutil2](https://github.com/Nandaka/PixivUtil2) configuration options). You should shutdown PixivUtil server and remove the backup `.ini` file before applying the changes and restarting.

### Environment Variable Configuration

Supported environment variable overrides. See `PixivServer/configuration/pixivutil.py`.

## Architecture and Development

PixivUtil server is a Python project based on PixivUtil2 as its API client engine. PixivUtil2 is a separate git repository added to this as a submodule.

PixivUtil server as a service consists of 3 microservices: the PixivUtil API server, PixivUtil worker, and RabbitMQ queue. The server receives API requests from the user/client, and passes them as long-running jobs to a single-process worker which handles them one at a time via the queue, controlling API volumes and avoiding rate limit violations.

The web server component uses FastAPI, and the worker component uses Celery listening to FastAPI publishes through a rabbit queue.

To support durable messages with RabbitMQ, a timeout configuration is applied for the queue server. See [issue](https://github.com/docker-library/rabbitmq/issues/106).

### Command Line Workflows

`uv` is the recommended Python project manager for development:

```sh
uv sync --extra dev --extra pixivutil2  # sync dev + PixivUtil2 dependencies
uv run pytest tests                     # run tests
uv run ruff check .                     # run ruff lint check
```

The project also uses `uv` as the build runtime with `uv_build`, which significantly speeds up build times. On a raspberry pi, building the Dockerfile with `uv_build` takes ~5m, 3m less than with default `pip`.
