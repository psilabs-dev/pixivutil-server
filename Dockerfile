FROM python:3.12-slim

LABEL org.opencontainers.image.authors="psilabs-dev <https://github.com/psilabs-dev>"
LABEL org.opencontainers.image.source="https://github.com/psilabs-dev/pixivutil-server"

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg sqlite3 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workdir

# Copy entire repo and install via pyproject
COPY . .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .
