import logging
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context

_log = logging.getLogger("alembic.env")

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_database_url() -> str:
    """Build DATABASE_URL from environment variables — never hardcode credentials."""
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.environ.get("POSTGRES_HOST", "db")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "homestock")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


config.set_main_option("sqlalchemy.url", get_database_url())

target_metadata = None

# Stable arbitrary key for the restore-recovery advisory lock. Must be unique
# within this PostgreSQL instance; chosen to avoid collision with any future
# application-level advisory locks.
_RECOVERY_ADVISORY_KEY = 8_897_641


def _check_restore_artifacts(connection) -> None:
    """
    Detect and recover from a server crash that occurred during a restore operation.

    The restore process renames homestock -> homestock_pre_restore before applying
    the backup SQL. If the process is killed in that window the live schema is gone
    but the data is safe under the temp name. We recover automatically on next start.

    A PostgreSQL session-level advisory lock serializes this check across multiple
    containers starting simultaneously (e.g. after a host crash or rolling restart).

    Two recovery cases:

    1. homestock_pre_restore exists, homestock does NOT
       -> crash between rename and restore start
       -> unambiguously safe to rename pre_restore back; original data fully intact
       -> auto-recover and continue normally

    2. both schemas exist
       -> either a previous successful restore where the final DROP failed,
          or a partial restore that created homestock before the process died
       -> homestock is the best available state; drop the stale pre_restore artifact
    """
    # Try to acquire an exclusive session-level advisory lock. If another container
    # already holds it (simultaneous startup), skip — they will do the recovery.
    locked = connection.execute(
        text("SELECT pg_try_advisory_lock(:key)"),
        {"key": _RECOVERY_ADVISORY_KEY},
    ).scalar()
    # Commit so the lock acquisition is visible; advisory locks persist for the
    # session regardless of subsequent transaction boundaries.
    connection.commit()

    if not locked:
        _log.info(
            "Startup recovery: another process holds the advisory lock — skipping."
        )
        return

    try:
        result = connection.execute(text(
            "SELECT nspname FROM pg_namespace "
            "WHERE nspname IN ('homestock', 'homestock_pre_restore')"
        ))
        schemas = {row[0] for row in result}

        if "homestock_pre_restore" not in schemas:
            return  # Nothing to recover — normal startup

        if "homestock" not in schemas:
            _log.critical(
                "STARTUP RECOVERY: 'homestock_pre_restore' exists but 'homestock' does not. "
                "The server likely crashed during a restore rename operation. "
                "Renaming 'homestock_pre_restore' -> 'homestock' to recover original data."
            )
            with connection.begin():
                connection.execute(
                    text("ALTER SCHEMA homestock_pre_restore RENAME TO homestock")
                )
            _log.info("Recovery complete — 'homestock' schema restored from pre-restore snapshot.")
        else:
            _log.warning(
                "Found stale schema 'homestock_pre_restore' alongside active 'homestock'. "
                "This is a leftover from a restore where the final cleanup step failed. "
                "Dropping the stale schema."
            )
            with connection.begin():
                connection.execute(text("DROP SCHEMA homestock_pre_restore CASCADE"))
            _log.info("Stale 'homestock_pre_restore' schema dropped.")
    finally:
        connection.execute(
            text("SELECT pg_advisory_unlock(:key)"),
            {"key": _RECOVERY_ADVISORY_KEY},
        )
        connection.commit()


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="homestock",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        _check_restore_artifacts(connection)
        # Pin the search_path so migration DDL that uses unqualified object names
        # resolves against the homestock schema. init.sql installs pg_trgm (and
        # its gin_trgm_ops operator class) into homestock; without this, Alembic
        # connects on the role's default search_path (public) and a first-run
        # CREATE INDEX ... gin (name gin_trgm_ops) fails to resolve the opclass.
        # Committed so the session-level SET survives the migration transaction.
        connection.execute(text("SET search_path TO homestock, public"))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="homestock",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
