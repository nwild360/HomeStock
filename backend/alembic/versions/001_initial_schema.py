"""Initial schema baseline

Revision ID: 001
Revises:
Create Date: 2026-04-16

Creates the full initial schema idempotently (all statements are IF NOT EXISTS
or equivalent).  On a normal fresh start init.sql has already created everything
and every statement here is a no-op.  On a schema-wiped database (e.g. after a
failed backup restore) this migration recreates the baseline so that migrations
002+ can continue applying correctly.
"""
from typing import Sequence, Union
from alembic import op

revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS homestock")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # CREATE DOMAIN has no IF NOT EXISTS — use a DO block
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type t
                JOIN pg_namespace n ON t.typnamespace = n.oid
                WHERE n.nspname = 'homestock' AND t.typname = 'item_type'
            ) THEN
                CREATE DOMAIN homestock.item_type AS TEXT
                    CHECK (lower(VALUE) IN ('food', 'household'));
            END IF;
        END $$
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS homestock.users (
            id               BIGSERIAL PRIMARY KEY,
            username         TEXT NOT NULL UNIQUE CHECK (
                                 length(username) BETWEEN 3 AND 50
                                 AND username ~ '^[a-zA-Z0-9_-]+$'
                             ),
            hashed_password  TEXT NOT NULL CHECK (length(hashed_password) >= 80)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS homestock.categories (
            id          BIGSERIAL PRIMARY KEY,
            name        TEXT NOT NULL UNIQUE CHECK (length(name) BETWEEN 1 AND 255),
            description TEXT CHECK (length(description) <= 1000)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS homestock.units (
            id           BIGSERIAL PRIMARY KEY,
            name         TEXT NOT NULL UNIQUE CHECK (length(name) BETWEEN 1 AND 255),
            abbreviation TEXT UNIQUE
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS homestock.items (
            id             BIGSERIAL PRIMARY KEY,
            name           TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 255),
            type           homestock.item_type NOT NULL,
            category_id    BIGINT REFERENCES homestock.categories(id) ON DELETE SET NULL,
            quantity       NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (quantity >= 0),
            unit_id        BIGINT REFERENCES homestock.units(id) ON DELETE SET NULL,
            notes          TEXT CHECK (length(notes) <= 1000),
            mealie_food_id TEXT UNIQUE CHECK (mealie_food_id ~ '^[A-Za-z0-9\\-_]{1,64}$'),
            created_at     TIMESTAMPTZ DEFAULT NOW(),
            updated_at     TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS homestock.jwt_blacklist (
            jti        TEXT PRIMARY KEY,
            username   TEXT NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            revoked_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_items_category_id ON homestock.items (category_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_items_unit_id ON homestock.items (unit_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_items_name_trgm ON homestock.items USING gin (name gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_expires_at ON homestock.jwt_blacklist (expires_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_username ON homestock.jwt_blacklist (username)")

    # CREATE OR REPLACE is idempotent for functions
    op.execute("""
        CREATE OR REPLACE FUNCTION homestock.update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            EXCEPTION
                WHEN OTHERS THEN
                    RAISE WARNING 'Error in update_updated_at_column trigger: %', SQLERRM;
                    RETURN NEW;
            END;
        END;
        $$ LANGUAGE plpgsql
    """)

    # Trigger has no IF NOT EXISTS before PG17 — use a DO block
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'update_items_updated_at'
            ) THEN
                CREATE TRIGGER update_items_updated_at
                    BEFORE UPDATE ON homestock.items
                    FOR EACH ROW
                    EXECUTE FUNCTION homestock.update_updated_at_column();
            END IF;
        END $$
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION homestock.cleanup_expired_jwt_tokens()
        RETURNS void AS $$
        BEGIN
            DELETE FROM homestock.jwt_blacklist WHERE expires_at < NOW();
        END;
        $$ LANGUAGE plpgsql
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS update_items_updated_at ON homestock.items")
    op.execute("DROP FUNCTION IF EXISTS homestock.update_updated_at_column()")
    op.execute("DROP FUNCTION IF EXISTS homestock.cleanup_expired_jwt_tokens()")
    op.execute("DROP TABLE IF EXISTS homestock.jwt_blacklist")
    op.execute("DROP TABLE IF EXISTS homestock.items")
    op.execute("DROP TABLE IF EXISTS homestock.units")
    op.execute("DROP TABLE IF EXISTS homestock.categories")
    op.execute("DROP TABLE IF EXISTS homestock.users")
    op.execute("DROP DOMAIN IF EXISTS homestock.item_type")
    op.execute("DROP SCHEMA IF EXISTS homestock")
