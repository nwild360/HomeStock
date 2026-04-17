"""OIDC support

Revision ID: 002
Revises: 001
Create Date: 2026-04-16

Changes:
- hashed_password: NOT NULL → nullable (OIDC users have no password)
- Drop length check constraint on hashed_password (argon2 length assumed)
- Add oidc_sub column (Keycloak subject claim, unique per user)
- Add oidc_provider column (e.g. "keycloak")
- Add CHECK: every user must have either hashed_password OR oidc_sub
- Add oidc_settings table for runtime OIDC configuration
"""
from typing import Sequence, Union
from alembic import op

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Allow OIDC users to have no password
    op.execute("ALTER TABLE homestock.users ALTER COLUMN hashed_password DROP NOT NULL")

    # The old constraint enforced argon2 hash length — no longer universally applicable
    op.execute("ALTER TABLE homestock.users DROP CONSTRAINT IF EXISTS users_hashed_password_check")

    # OIDC identity columns
    op.execute("ALTER TABLE homestock.users ADD COLUMN IF NOT EXISTS oidc_sub TEXT")
    op.execute("ALTER TABLE homestock.users ADD COLUMN IF NOT EXISTS oidc_provider TEXT")

    # Partial unique index: oidc_sub must be unique when set, but NULL rows are allowed
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS users_oidc_sub_unique
            ON homestock.users (oidc_sub)
            WHERE oidc_sub IS NOT NULL
    """)

    # Every user must authenticate via password or OIDC — not neither
    op.execute("""
        ALTER TABLE homestock.users
            ADD CONSTRAINT users_auth_method_check
            CHECK (hashed_password IS NOT NULL OR oidc_sub IS NOT NULL)
    """)

    # Runtime OIDC configuration stored in DB so the admin can toggle without restart
    op.execute("""
        CREATE TABLE IF NOT EXISTS homestock.oidc_settings (
            id          BIGSERIAL PRIMARY KEY,
            enabled     BOOLEAN   NOT NULL DEFAULT FALSE,
            issuer_url  TEXT,
            client_id   TEXT,
            client_secret TEXT,
            redirect_uri TEXT,
            updated_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Seed one disabled row — the app always reads row id=1
    op.execute("INSERT INTO homestock.oidc_settings (enabled) VALUES (FALSE)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS homestock.oidc_settings")
    op.execute("ALTER TABLE homestock.users DROP CONSTRAINT IF EXISTS users_auth_method_check")
    op.execute("DROP INDEX IF EXISTS homestock.users_oidc_sub_unique")
    op.execute("ALTER TABLE homestock.users DROP COLUMN IF EXISTS oidc_provider")
    op.execute("ALTER TABLE homestock.users DROP COLUMN IF EXISTS oidc_sub")
    op.execute("ALTER TABLE homestock.users ALTER COLUMN hashed_password SET NOT NULL")
    op.execute("""
        ALTER TABLE homestock.users
            ADD CONSTRAINT users_hashed_password_check
            CHECK (length(hashed_password) >= 80)
    """)
