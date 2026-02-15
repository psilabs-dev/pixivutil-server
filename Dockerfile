# syntax=docker/dockerfile:1.7
FROM astral/uv:python3.14-bookworm-slim

LABEL org.opencontainers.image.authors="psilabs-dev <https://github.com/psilabs-dev>"
LABEL org.opencontainers.image.source="https://github.com/psilabs-dev/pixivutil-server"

ENV DEBIAN_FRONTEND=noninteractive
ENV UV_NO_DEV=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends ffmpeg sqlite3 gosu && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workdir

# Install dependencies
COPY --link pyproject.toml                      /workdir/
COPY --link uv.lock                             /workdir/
COPY --link README.md                           /workdir/
COPY --link PixivServerCommon/pyproject.toml    /workdir/PixivServerCommon/pyproject.toml
COPY --link PixivUtilClient/pyproject.toml      /workdir/PixivUtilClient/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --extra pixivutil2 --locked --no-install-workspace --no-editable --compile-bytecode

# Copy project files and install the project
COPY --link LICENSE                             /workdir/
COPY --link PixivServerCommon                   /workdir/PixivServerCommon
COPY --link PixivServer                         /workdir/PixivServer
COPY --link PixivUtil2                          /workdir/PixivUtil2
COPY --link PixivUtilClient                     /workdir/PixivUtilClient
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --extra pixivutil2 --locked --no-editable --compile-bytecode && \
    rm -rf /workdir/PixivUtil2/test /workdir/PixivUtil2/test_data && \
    rm -rf /workdir/PixivUtilClient/tests

ENV PATH="/workdir/.venv/bin:$PATH"

# Create default user/group (UID/GID may be overridden at runtime)
RUN groupadd -g 1000 pixivuser && useradd -m -u 1000 -g pixivuser -s /bin/sh pixivuser

COPY --link docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
