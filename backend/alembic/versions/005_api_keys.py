"""Add api_keys table

Revision ID: 005
Revises: 004
Create Date: 2026-06-29

Changes:
- Add homestock.api_keys table for per-user programmatic API keys
"""
from typing import Sequence, Union
from alembic import op

revision: str = "005"
down_revision: Union[str, Sequence[str], None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS homestock.api_keys (
            id           BIGSERIAL PRIMARY KEY,
            user_id      BIGINT NOT NULL REFERENCES homestock.users(id) ON DELETE CASCADE,
            label        TEXT NOT NULL CHECK (length(label) BETWEEN 1 AND 100),
            key_hash     TEXT NOT NULL UNIQUE,   -- SHA-256 hex of the plaintext key
            key_prefix   TEXT NOT NULL,          -- non-secret display prefix
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_used_at TIMESTAMPTZ
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_api_keys_user_id "
        "ON homestock.api_keys (user_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS homestock.api_keys")
