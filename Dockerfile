FROM astral/uv:python3.14-bookworm-slim

LABEL org.opencontainers.image.authors="psilabs-dev <https://github.com/psilabs-dev>"
LABEL org.opencontainers.image.source="https://github.com/psilabs-dev/pixivutil-server"

ENV DEBIAN_FRONTEND=noninteractive
ENV UV_NO_DEV=1

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg sqlite3 gosu && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workdir

# Install dependencies
COPY pyproject.toml /workdir/
COPY uv.lock /workdir/
COPY README.md /workdir/
COPY PixivClient/pyproject.toml /workdir/PixivClient/pyproject.toml
RUN uv sync --extra pixivutil2 --locked --no-install-workspace

# Copy project files and install the project
COPY . /workdir
RUN uv sync --extra pixivutil2 --locked

# Create default user/group (UID/GID may be overridden at runtime)
RUN groupadd -g 1000 pixivuser && useradd -m -u 1000 -g pixivuser -s /bin/sh pixivuser

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
