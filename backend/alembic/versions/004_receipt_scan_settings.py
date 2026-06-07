"""Add receipt_scan_settings table

Revision ID: 004
Revises: 003
Create Date: 2026-04-25

Changes:
- Add homestock.receipt_scan_settings singleton table for AI receipt scan config
"""
from typing import Sequence, Union
from alembic import op

revision: str = "004"
down_revision: Union[str, Sequence[str], None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS homestock.receipt_scan_settings (
            id           BIGSERIAL PRIMARY KEY,
            enabled      BOOLEAN   NOT NULL DEFAULT FALSE,
            provider     TEXT      CHECK (provider IN ('claude', 'ollama')),
            api_key      TEXT,
            model        TEXT,
            endpoint_url TEXT,
            updated_at   TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute(
        "INSERT INTO homestock.receipt_scan_settings (enabled) "
        "SELECT FALSE WHERE NOT EXISTS (SELECT 1 FROM homestock.receipt_scan_settings WHERE id = 1)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS homestock.receipt_scan_settings")
