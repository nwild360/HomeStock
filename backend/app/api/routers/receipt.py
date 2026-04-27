"""
Receipt scan router: AI-powered receipt parsing and admin settings.

Endpoints:
  GET  /api/receipt/config    — public: is receipt scan enabled?
  GET  /api/receipt/settings  — admin: read full settings
  PUT  /api/receipt/settings  — admin: save settings
  POST /api/receipt/scan      — authenticated: upload image, get candidate items
"""
import logging
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
    """Read full receipt scan settings (admin)."""
    cfg = receipt_scan_service.get_receipt_scan_settings(db)
    if cfg is None:
        return ReceiptScanSettings(enabled=False)
    return cfg


@router.put("/settings", response_model=ReceiptScanSettings)
def update_receipt_settings(
    new_settings: ReceiptScanSettings,
    db: Session = Depends(get_dbsession),
    _user=Depends(require_auth),
):
    """Save receipt scan settings (admin). Validates required fields when enabled."""
    if new_settings.enabled:
        missing = []
        if not new_settings.provider:
            missing.append("provider")
        if not new_settings.model:
            missing.append("model")
        if new_settings.provider == "claude" and not new_settings.api_key:
            missing.append("api_key")
        if new_settings.provider == "ollama" and not new_settings.endpoint_url:
            missing.append("endpoint_url")
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing required fields to enable receipt scan: {', '.join(missing)}",
            )
    receipt_scan_service.save_receipt_scan_settings(db, new_settings)
    return new_settings


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
