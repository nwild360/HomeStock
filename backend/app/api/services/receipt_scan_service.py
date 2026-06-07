"""
Receipt scan service: DB helpers and AI provider dispatch.
"""
import base64
import json
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.schemas import ReceiptScanSettings, CandidateItem

logger = logging.getLogger(__name__)

RECEIPT_SCAN_PROMPT = """You are a receipt parser. Extract all distinct purchasable items from this receipt image.
Return ONLY valid JSON matching this exact schema — no markdown, no explanation, no extra keys:
{"items": [{"item_name": "string", "item_type": "food or household", "category_name": "string or null", "quantity": number, "unit_name": "string or null", "notes": "string or null"}]}
Rules:
- item_type must be exactly "food" or "household"
- quantity must be a positive number; default to 1 if unclear
- category_name: infer a general category (e.g. "Dairy", "Cleaning", "Produce", "Beverages") or null if unclear
- unit_name: infer from context (e.g. "oz", "lb", "pack") or null
- Omit receipt metadata: totals, taxes, subtotals, store name, dates, payment info
- If the image is not a receipt or no items can be found, return {"items": []}"""


class ReceiptScanError(Exception):
    pass


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_receipt_scan_settings(db: Session) -> Optional[ReceiptScanSettings]:
    """Read receipt scan settings from DB row id=1. Returns None if table is empty."""
    row = db.execute(
        text(
            "SELECT enabled, provider, api_key, model, endpoint_url "
            "FROM homestock.receipt_scan_settings WHERE id = 1"
        )
    ).first()
    if row is None:
        return None
    return ReceiptScanSettings(
        enabled=row.enabled,
        provider=row.provider,
        api_key=row.api_key,
        model=row.model,
        endpoint_url=row.endpoint_url,
    )


def save_receipt_scan_settings(db: Session, settings: ReceiptScanSettings) -> None:
    """Update receipt scan settings in row id=1.
    api_key is preserved from the existing row when settings.api_key is None."""
    db.execute(
        text("""
            UPDATE homestock.receipt_scan_settings
               SET enabled      = :enabled,
                   provider     = :provider,
                   api_key      = COALESCE(:api_key, api_key),
                   model        = :model,
                   endpoint_url = :endpoint_url,
                   updated_at   = NOW()
             WHERE id = 1
        """),
        {
            "enabled": settings.enabled,
            "provider": settings.provider,
            "api_key": settings.api_key,
            "model": settings.model,
            "endpoint_url": settings.endpoint_url,
        },
    )
    db.commit()


# ---------------------------------------------------------------------------
# JSON cleanup helper
# ---------------------------------------------------------------------------

def _parse_json_response(raw: str) -> dict:
    """Strip markdown fences and parse JSON. Raises ReceiptScanError on failure."""
    cleaned = raw.strip()
    # Strip ```json ... ``` or ``` ... ``` fences
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse AI response as JSON: %s\nRaw: %.500s", e, raw)
        raise ReceiptScanError("AI returned unparseable response") from e


# ---------------------------------------------------------------------------
# Claude provider
# ---------------------------------------------------------------------------

def scan_with_claude(image_bytes: bytes, mime_type: str, settings: ReceiptScanSettings) -> list[CandidateItem]:
    try:
        import anthropic
    except ImportError as e:
        raise ReceiptScanError("anthropic package is not installed") from e

    client = anthropic.Anthropic(api_key=settings.api_key)
    b64_image = base64.standard_b64encode(image_bytes).decode("utf-8")

    try:
        message = client.messages.create(
            model=settings.model,
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": b64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": RECEIPT_SCAN_PROMPT,
                        },
                    ],
                }
            ],
        )
    except Exception as e:
        raise ReceiptScanError(f"Claude API error: {e}") from e

    raw = message.content[0].text if message.content else ""
    data = _parse_json_response(raw)
    return _validate_items(data)


# ---------------------------------------------------------------------------
# Ollama provider
# ---------------------------------------------------------------------------

def scan_with_ollama(image_bytes: bytes, mime_type: str, settings: ReceiptScanSettings) -> list[CandidateItem]:
    try:
        import httpx
    except ImportError as e:
        raise ReceiptScanError("httpx package is not installed") from e

    if not settings.endpoint_url:
        raise ReceiptScanError("Ollama endpoint_url is not configured")
    b64_image = base64.standard_b64encode(image_bytes).decode("utf-8")
    endpoint = settings.endpoint_url.rstrip("/")

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{endpoint}/api/generate",
                json={
                    "model": settings.model,
                    "prompt": RECEIPT_SCAN_PROMPT,
                    "images": [b64_image],
                    "stream": False,
                    "format": "json",
                },
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise ReceiptScanError(f"Ollama returned HTTP {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise ReceiptScanError(f"Could not reach Ollama at {endpoint}: {e}") from e

    raw = response.json().get("response", "")
    data = _parse_json_response(raw)
    return _validate_items(data)


# ---------------------------------------------------------------------------
# Item validation
# ---------------------------------------------------------------------------

def _validate_items(data: dict) -> list[CandidateItem]:
    """Convert raw parsed dict to validated CandidateItem list. Skips malformed rows."""
    raw_items = data.get("items", [])
    if not isinstance(raw_items, list):
        return []

    results = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        item_type = raw.get("item_type", "").lower()
        if item_type not in ("food", "household"):
            item_type = "food"
        try:
            results.append(
                CandidateItem(
                    item_name=str(raw.get("item_name", "Unknown Item"))[:255],
                    item_type=item_type,
                    category_name=raw.get("category_name") or None,
                    quantity=float(raw.get("quantity", 1)) if raw.get("quantity") else 1,
                    unit_name=raw.get("unit_name") or None,
                    notes=raw.get("notes") or None,
                )
            )
        except Exception as e:
            logger.warning("Skipping malformed candidate item %s: %s", raw, e)
    return results


# ---------------------------------------------------------------------------
# Dispatch entry point
# ---------------------------------------------------------------------------

def scan_receipt(db: Session, image_bytes: bytes, mime_type: str) -> list[CandidateItem]:
    """Fetch settings, dispatch to the configured AI provider, return candidate items."""
    settings = get_receipt_scan_settings(db)
    if settings is None or not settings.enabled:
        raise ReceiptScanError("Receipt scanning is not enabled")

    if settings.provider == "claude":
        return scan_with_claude(image_bytes, mime_type, settings)
    elif settings.provider == "ollama":
        return scan_with_ollama(image_bytes, mime_type, settings)
    else:
        raise ReceiptScanError(f"Unknown provider: {settings.provider}")
