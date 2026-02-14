#!/usr/bin/env sh
set -eu

USER_ID="${PUID:-1000}"
GROUP_ID="${PGID:-1000}"

echo "Starting with UID: ${USER_ID}, GID: ${GROUP_ID}"

# Create group for GROUP_ID if none exists.
if ! getent group "${GROUP_ID}" >/dev/null 2>&1; then
  echo "Creating group with GID: ${GROUP_ID}"
  groupadd -g "${GROUP_ID}" appuser
fi

# Create user for USER_ID if none exists.
if ! getent passwd "${USER_ID}" >/dev/null 2>&1; then
  echo "Creating user with UID: ${USER_ID}"
  group_name="$(getent group "${GROUP_ID}" | cut -d: -f1)"
  useradd -u "${USER_ID}" -g "${group_name}" -s /bin/sh -d /workdir -m appuser
fi

# Ensure writable paths exist and are owned by runtime UID/GID.
mkdir -p /workdir/.pixivUtil2 /workdir/downloads
chown -R "${USER_ID}:${GROUP_ID}" \
  /workdir/.pixivUtil2 \
  /workdir/downloads \
  /workdir/.venv \
  /workdir/PixivUtil2 \
  /workdir 2>/dev/null || true

# Run command as runtime UID/GID.
if [ "$(id -u)" = "0" ]; then
  exec gosu "${USER_ID}:${GROUP_ID}" uv run "$@"
else
  exec uv run "$@"
fi
