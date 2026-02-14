# PixivUtil Server

PixivUtil server is a self-hosted, containerized server solution which provides [PixivUtil2](https://github.com/Nandaka/PixivUtil2) content download operations through an HTTP API interface.

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
curl -X POST http://localhost:8000/api/queue/download/artwork/{artwork-id-here}
```

`/api/download/*` remains available as a deprecated compatibility alias.

If `PIXIVUTIL_SERVER_API_KEY` is not set (or is empty), API key authentication is disabled.

An nginx [configuration file](/nginx/default.conf) is attached for your reverse proxy reference.

### API Reference

#### [Database](/docs/api/database.md)

Endpoints to get metadata from the PixivUtil2 database.

For example, the server supports the following endpoints:

- Get image metadata by ID
- Get member metadata by ID
- Get tag metadata by ID
- Get series metadata by ID

#### [Download queueing](/docs/api/download.md)

API endpoints to queue content (artwork) downloads for worker from server.

The following jobs are supported via PixivUtil server API:

- Download artworks by member ID
- Download artwork by image ID
- Download artworks by tag

#### [Health](/docs/api/health.md)

Health-related API endpoints, such as healthcheck for Docker containers.

#### [Metadata queueing](/docs/api/metadata.md)

API endpoints to queue metadata downloads for worker from server. Metadata includes artist, artwork, series, and tag.

This is helpful when you have an artwork downloaded, but it's old/outdated and you want to re-fetch only the metadata.

#### [Server](/docs/api/server.md)

Server-related API endpoints, such as get cookie, update cookie, delete database, and delete downloads.

## Configuration

PixivUtil server applies a downstream server flavor of PixivUtil2 called "Server Mode" [PixivUtil2](https://github.com/psilabs-dev/PixivUtil2). Server Mode applies additional configuration changes to ensure that downloaded Pixiv data is more reliable and available. See the server mode README [here](https://github.com/psilabs-dev/PixivUtil2/blob/server-mode/main/SERVER_README.md).

For further configuration, apply them at `.pixivUtil2/conf/conf.ini` (refer to [Pixivutil2](https://github.com/Nandaka/PixivUtil2) configuration options). You should shutdown PixivUtil server and remove the backup `.ini` file before applying the changes and restarting.

Supported environment variable overrides. See `PixivServer/configuration/pixivutil.py`.

### User Configuration

Docker user mapping:
- `PUID` and `PGID` set the UID/GID used by the server and worker containers (default `1000:1000`).

Any directories that were previously root should be set to the desired UID/GID pair.

If there are file permission issues, you may override the user entrypoint and maintain the container user as root.

```yaml
entrypoint: ["uv", "run"] # use this if you want to keep a non-root user.
```

### API Authentication

Set `PIXIVUTIL_SERVER_API_KEY` to enable API key authentication for protected endpoints.

Header format:

```text
Authorization: Bearer <your-api-key>
```

## Architecture and Development

PixivUtil server is a Python project based on PixivUtil2 as its API client engine. PixivUtil2 is a separate git repository added to this as a submodule.

PixivUtil server as a service consists of 3 microservices: the PixivUtil API server, PixivUtil worker, and RabbitMQ queue. The server receives API requests from the user/client, and passes them as long-running jobs to a single-process worker which handles them one at a time via the queue, controlling API volumes and avoiding rate limit violations.

The web server component uses FastAPI, and the worker component uses Celery listening to FastAPI publishes through a rabbit queue.

To support durable messages with RabbitMQ, a timeout configuration is applied for the queue server. See [issue](https://github.com/docker-library/rabbitmq/issues/106).

### Command Line Workflows

`uv` is the recommended Python project manager for development:

```sh
uv sync --extra pixivutil2              # sync dev + PixivUtil2 dependencies
uv run pytest tests                     # run tests
uv run ruff check .                     # run ruff lint check
```

The project also uses `uv` as the build runtime with `uv_build`, which significantly speeds up build times. On a raspberry pi, building the Dockerfile with `uv_build` takes ~5m, 3m less than with default `pip`.

## PixivUtil Client

PixivUtil client is an asynchronous API client for PixivUtil server. See the client [README](/PixivUtilClient/README.md).
