"""
MCP router: admin settings for the MCP server feature + OAuth resource metadata.

Endpoints:
  GET /api/mcp/config    — public: is the MCP server enabled?
  GET /api/mcp/settings  — admin: read full settings
  PUT /api/mcp/settings  — admin: save settings

  GET /.well-known/oauth-protected-resource       — RFC 9728 metadata (well_known_router)
  GET /.well-known/oauth-protected-resource/mcp   — RFC 9728 path-suffix form

The MCP protocol endpoint itself is mounted separately at /mcp (see main.py).
"""
import logging
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.schemas import McpConfig, McpSettings
from app.api.services import mcp_settings_service, oidc_service
from app.dependencies.db_session import get_dbsession
from app.dependencies.auth import require_auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mcp", tags=["mcp"])
well_known_router = APIRouter(tags=["mcp"])


# ---------------------------------------------------------------------------
# Public config
# ---------------------------------------------------------------------------

@router.get("/config", response_model=McpConfig)
def mcp_config(db: Session = Depends(get_dbsession)):
    """Return whether the MCP server is enabled (no details exposed)."""
    cfg = mcp_settings_service.get_mcp_settings(db)
    return McpConfig(enabled=bool(cfg and cfg.enabled))


# ---------------------------------------------------------------------------
# Admin settings
# ---------------------------------------------------------------------------

@router.get("/settings", response_model=McpSettings)
def get_mcp_settings(
    db: Session = Depends(get_dbsession),
    _user=Depends(require_auth),
):
    """Read MCP server settings."""
    cfg = mcp_settings_service.get_mcp_settings(db)
    if cfg is None:
        return McpSettings(enabled=False)
    return cfg


@router.put("/settings", response_model=McpSettings)
def put_mcp_settings(
    settings: McpSettings,
    db: Session = Depends(get_dbsession),
    _user=Depends(require_auth),
):
    """Save MCP server settings."""
    if settings.enabled:
        if settings.server_url:
            parsed = urlparse(settings.server_url)
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="server_url must be a valid http(s) URL",
                )
        # At least one auth method must be viable: OAuth via OIDC, or API keys
        oidc = oidc_service.get_oidc_settings(db)
        oidc_ready = bool(oidc and oidc.enabled and oidc.issuer_url)
        if not oidc_ready and not settings.allow_api_keys:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Enable SSO/OIDC or allow API key auth — otherwise no agent could authenticate",
            )
        if oidc_ready and not settings.server_url:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="server_url is required for OAuth (it is the token audience)",
            )
    mcp_settings_service.save_mcp_settings(db, settings)
    saved = mcp_settings_service.get_mcp_settings(db)
    logger.info("MCP settings updated: enabled=%s allow_api_keys=%s", saved.enabled, saved.allow_api_keys)
    return saved


# ---------------------------------------------------------------------------
# OAuth 2.0 Protected Resource Metadata (RFC 9728)
# ---------------------------------------------------------------------------

def _protected_resource_metadata(db: Session) -> dict:
    cfg = mcp_settings_service.get_mcp_settings(db)
    if cfg is None or not cfg.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server is not enabled")
    oidc = oidc_service.get_oidc_settings(db)
    if not (oidc and oidc.enabled and oidc.issuer_url) or not cfg.server_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OAuth is not configured for the MCP server")
    return {
        "resource": cfg.server_url,
        "authorization_servers": [oidc.issuer_url],
        "scopes_supported": [cfg.required_scope] if cfg.required_scope else [],
        "bearer_methods_supported": ["header"],
    }


@well_known_router.get("/.well-known/oauth-protected-resource")
def oauth_protected_resource(db: Session = Depends(get_dbsession)):
    """RFC 9728 Protected Resource Metadata for the MCP endpoint."""
    return _protected_resource_metadata(db)


@well_known_router.get("/.well-known/oauth-protected-resource/mcp")
def oauth_protected_resource_mcp(db: Session = Depends(get_dbsession)):
    """RFC 9728 path-suffix form: metadata for the resource at /mcp."""
    return _protected_resource_metadata(db)
