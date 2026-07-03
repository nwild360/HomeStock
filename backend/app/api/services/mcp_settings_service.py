"""
MCP settings service: DB helpers for the mcp_settings singleton row.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.schemas import McpSettings

logger = logging.getLogger(__name__)


def get_mcp_settings(db: Session) -> Optional[McpSettings]:
    """Read MCP settings from DB row id=1. Returns None if table is empty."""
    row = db.execute(
        text(
            "SELECT enabled, allow_api_keys, server_url, required_scope "
            "FROM homestock.mcp_settings WHERE id = 1"
        )
    ).first()
    if row is None:
        return None
    return McpSettings(
        enabled=row.enabled,
        allow_api_keys=row.allow_api_keys,
        server_url=row.server_url,
        required_scope=row.required_scope,
    )


def save_mcp_settings(db: Session, settings: McpSettings) -> None:
    """Update MCP settings in row id=1."""
    db.execute(
        text("""
            UPDATE homestock.mcp_settings
               SET enabled        = :enabled,
                   allow_api_keys = :allow_api_keys,
                   server_url     = :server_url,
                   required_scope = :required_scope,
                   updated_at     = NOW()
             WHERE id = 1
        """),
        {
            "enabled": settings.enabled,
            "allow_api_keys": settings.allow_api_keys,
            "server_url": settings.server_url,
            "required_scope": settings.required_scope,
        },
    )
    db.commit()


def is_mcp_enabled(db: Session) -> bool:
    """Cheap boolean check used by the MCP auth middleware on every request."""
    enabled = db.execute(
        text("SELECT enabled FROM homestock.mcp_settings WHERE id = 1")
    ).scalar()
    return bool(enabled)
