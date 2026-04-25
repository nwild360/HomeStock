"""Add expiration_date and date_bought to items

Revision ID: 003
Revises: 002
Create Date: 2026-04-24

Changes:
- Add expiration_date DATE (nullable) — intended for food items
- Add date_bought DATE (nullable) — intended for household items
- Both columns are unrestricted by type so either can be used on any item type in future
"""
from typing import Sequence, Union
from alembic import op

revision: str = "003"
down_revision: Union[str, Sequence[str], None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE homestock.items ADD COLUMN IF NOT EXISTS expiration_date DATE")
    op.execute("ALTER TABLE homestock.items ADD COLUMN IF NOT EXISTS date_bought DATE")


def downgrade() -> None:
    op.execute("ALTER TABLE homestock.items DROP COLUMN IF EXISTS date_bought")
    op.execute("ALTER TABLE homestock.items DROP COLUMN IF EXISTS expiration_date")
