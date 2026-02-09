FROM astral/uv:python3.14-bookworm-slim

LABEL org.opencontainers.image.authors="psilabs-dev <https://github.com/psilabs-dev>"
LABEL org.opencontainers.image.source="https://github.com/psilabs-dev/pixivutil-server"

ENV DEBIAN_FRONTEND=noninteractive
ENV UV_NO_DEV=1

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg sqlite3 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workdir

# Install dependencies
COPY pyproject.toml /workdir/
COPY uv.lock /workdir/
COPY README.md /workdir/
RUN uv sync --extra pixivutil2 --locked --no-install-project

# Copy project files and install the project
COPY . /workdir
RUN uv sync --extra pixivutil2 --locked

ENTRYPOINT ["uv", "run"]
