#!/bin/sh
set -e

# The container starts as root SOLELY to normalize ownership of the backups
# volume, then immediately drops to the unprivileged 'appuser' via gosu before
# running the app -- the same root-chown-then-drop pattern the official Postgres
# image uses. Docker does not chown bind-mounted volumes, so /app/backups can
# arrive root-owned; fixing it here on every boot keeps the non-root app able to
# write backups regardless of how the volume was created or where it's deployed.
BACKUP_DIR="${BACKUP_STORAGE_PATH:-/app/backups}"
mkdir -p "$BACKUP_DIR"
chown -R appuser:appuser "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

# Drop from root to appuser and exec the real command (CMD).
exec gosu appuser "$@"
