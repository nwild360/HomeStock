"""Initial schema baseline

Revision ID: 001
Revises:
Create Date: 2026-04-16

This migration represents the schema created by db/init.sql.
It performs no SQL — its purpose is to give Alembic a starting point
so future migrations can chain from it.

On a fresh database: upgrade() runs but does nothing (init.sql already ran).
On existing production: run `alembic stamp 001` once to register this
revision without executing anything, then future migrations apply normally.
"""
from typing import Sequence, Union

revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
