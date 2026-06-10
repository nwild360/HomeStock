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

# Wait for Postgres to actually accept TCP connections before the CMD runs its
# migrations. `depends_on: service_healthy` is not sufficient on a fresh volume:
# during first-time init the Postgres image runs a temporary socket-only server
# while executing init.sql, which makes the container's own `pg_isready`
# healthcheck pass before TCP is up -- so alembic would race in and hit
# "connection refused". Poll the real host:port over TCP instead.
DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
echo "Waiting for database at ${DB_HOST}:${DB_PORT}..."
i=0
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -ge 60 ]; then
    echo "Database not ready after 60s, giving up." >&2
    exit 1
  fi
  sleep 1
done
echo "Database is ready."

# Drop from root to appuser and exec the real command (CMD).
exec gosu appuser "$@"
