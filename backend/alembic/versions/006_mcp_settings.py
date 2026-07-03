"""Add mcp_settings table

Revision ID: 006
Revises: 005
Create Date: 2026-07-02

Changes:
- Add homestock.mcp_settings singleton table for the MCP server feature toggle
"""
from typing import Sequence, Union
from alembic import op

revision: str = "006"
down_revision: Union[str, Sequence[str], None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS homestock.mcp_settings (
            id             BIGSERIAL PRIMARY KEY,
            enabled        BOOLEAN NOT NULL DEFAULT FALSE,
            allow_api_keys BOOLEAN NOT NULL DEFAULT FALSE,
            server_url     TEXT,                             -- canonical public MCP URL (OAuth audience/resource id)
            required_scope TEXT DEFAULT 'mcp:tools',
            updated_at     TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute(
        "INSERT INTO homestock.mcp_settings (enabled) "
        "SELECT FALSE WHERE NOT EXISTS (SELECT 1 FROM homestock.mcp_settings WHERE id = 1)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS homestock.mcp_settings")
