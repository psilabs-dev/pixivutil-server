#!/usr/bin/env sh
set -eu

APP_USER=app
APP_GROUP=app

PUID="${PUID:-1000}"
PGID="${PGID:-1000}"

# Ensure group exists with desired GID
if ! getent group "${APP_GROUP}" >/dev/null 2>&1; then
  groupadd -g "${PGID}" "${APP_GROUP}"
else
  groupmod -o -g "${PGID}" "${APP_GROUP}"
fi

# Ensure user exists with desired UID/GID
if ! id -u "${APP_USER}" >/dev/null 2>&1; then
  useradd -m -u "${PUID}" -g "${APP_GROUP}" -s /bin/sh "${APP_USER}"
else
  usermod -o -u "${PUID}" -g "${APP_GROUP}" "${APP_USER}"
fi

# Fix ownership of writable paths (ignore failures for first-run bind mounts)
chown -R "${PUID}:${PGID}" \
  /workdir/.pixivUtil2 \
  /workdir/downloads \
  /workdir/.venv \
  /workdir/PixivUtil2 \
  /workdir 2>/dev/null || true

# Entrypoint command
exec gosu "${PUID}:${PGID}" uv run "$@"
