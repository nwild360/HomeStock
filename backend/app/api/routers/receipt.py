"""
Receipt scan router: AI-powered receipt parsing and admin settings.

Endpoints:
  GET  /api/receipt/config    — public: is receipt scan enabled?
  GET  /api/receipt/settings  — admin: read full settings
  PUT  /api/receipt/settings  — admin: save settings
  POST /api/receipt/scan      — authenticated: upload image, get candidate items
"""
import logging
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.api.schemas import ReceiptScanConfig, ReceiptScanSettings, ReceiptScanResponse
from app.api.services import receipt_scan_service
from app.dependencies.db_session import get_dbsession
from app.dependencies.auth import require_auth

limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/receipt", tags=["receipt"])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB

# Cloud/link-local metadata IPs that must never be reachable via SSRF
_BLOCKED_HOSTS = {"169.254.169.254", "metadata.google.internal", "metadata.internal"}


def _validate_ollama_url(url: str) -> None:
    """Reject non-http(s) schemes and known cloud metadata endpoints."""
    try:
        parsed = urlparse(url)
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid endpoint URL")
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="endpoint_url must use http or https",
        )
    if parsed.hostname in _BLOCKED_HOSTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="endpoint_url points to a reserved address",
        )


# ---------------------------------------------------------------------------
# Public config
# ---------------------------------------------------------------------------

@router.get("/config", response_model=ReceiptScanConfig)
def receipt_config(db: Session = Depends(get_dbsession)):
    """Return whether receipt scanning is enabled (no credentials exposed)."""
    cfg = receipt_scan_service.get_receipt_scan_settings(db)
    if cfg is None or not cfg.enabled:
        return ReceiptScanConfig(enabled=False)
    return ReceiptScanConfig(enabled=True)


# ---------------------------------------------------------------------------
# Admin settings
# ---------------------------------------------------------------------------

@router.get("/settings", response_model=ReceiptScanSettings)
def get_receipt_settings(
    db: Session = Depends(get_dbsession),
    _user=Depends(require_auth),
):
    """Read receipt scan settings. api_key is never returned — submit a new value to update it."""
    cfg = receipt_scan_service.get_receipt_scan_settings(db)
    if cfg is None:
        return ReceiptScanSettings(enabled=False)
    return ReceiptScanSettings(
        enabled=cfg.enabled,
        provider=cfg.provider,
        api_key=None,
        model=cfg.model,
        endpoint_url=cfg.endpoint_url,
    )


@router.put("/settings", response_model=ReceiptScanSettings)
def update_receipt_settings(
    new_settings: ReceiptScanSettings,
    db: Session = Depends(get_dbsession),
    _user=Depends(require_auth),
):
    """Save receipt scan settings (admin). Validates required fields when enabled."""
    if new_settings.provider == "ollama" and new_settings.endpoint_url:
        _validate_ollama_url(new_settings.endpoint_url)

    if new_settings.enabled:
        # For Claude: api_key may be null if the user is leaving the existing key unchanged.
        # Fetch current settings to check whether a key is already stored.
        existing = receipt_scan_service.get_receipt_scan_settings(db)
        has_existing_key = bool(existing and existing.api_key)
        missing = []
        if not new_settings.provider:
            missing.append("provider")
        if not new_settings.model:
            missing.append("model")
        if new_settings.provider == "claude" and not new_settings.api_key and not has_existing_key:
            missing.append("api_key")
        if new_settings.provider == "ollama" and not new_settings.endpoint_url:
            missing.append("endpoint_url")
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing required fields to enable receipt scan: {', '.join(missing)}",
            )
    receipt_scan_service.save_receipt_scan_settings(db, new_settings)
    return ReceiptScanSettings(
        enabled=new_settings.enabled,
        provider=new_settings.provider,
        api_key=None,
        model=new_settings.model,
        endpoint_url=new_settings.endpoint_url,
    )


# ---------------------------------------------------------------------------
# Scan endpoint (Phase 2 — AI logic added here)
# ---------------------------------------------------------------------------

@router.post("/scan", response_model=ReceiptScanResponse)
@limiter.limit("5/minute")
async def scan_receipt(
    request: Request,
    image: UploadFile = File(...),
    db: Session = Depends(get_dbsession),
    _user=Depends(require_auth),
):
    """Upload a receipt image; returns AI-parsed candidate items."""
    cfg = receipt_scan_service.get_receipt_scan_settings(db)
    if cfg is None or not cfg.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt scanning is not enabled")

    if image.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported image type '{image.content_type}'. Allowed: jpeg, png, webp",
        )

    image_bytes = await image.read()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image must be 10 MB or smaller",
        )

    try:
        items = receipt_scan_service.scan_receipt(db, image_bytes, image.content_type)
    except receipt_scan_service.ReceiptScanError as e:
        logger.error("Receipt scan failed: %s", e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    return ReceiptScanResponse(items=items)
