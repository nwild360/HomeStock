"""
API keys service: mint, list, delete and resolve per-user programmatic API keys.

Keys are high-entropy random tokens. Only a SHA-256 hash is stored (deterministic so
it can be looked up by value); the plaintext is shown to the user exactly once at
creation. A non-secret prefix is stored for display in the management UI.
"""
import hashlib
import secrets
from typing import Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.schemas import ApiKeyOut, ApiKeyCreated

# Human-recognizable prefix on every minted key, followed by url-safe random.
KEY_PREFIX = "hs_live_"
# Number of leading chars stored/displayed as the non-secret identifier.
PREFIX_DISPLAY_LEN = 12


def _hash_key(plaintext: str) -> str:
    """SHA-256 hex digest of a plaintext key (high-entropy → SHA-256 is sufficient)."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def create_api_key(db: Session, user_id: int, label: str) -> ApiKeyCreated:
    """Mint a new API key for a user. Returns the row plus the one-time plaintext key."""
    plaintext = KEY_PREFIX + secrets.token_urlsafe(32)
    key_hash = _hash_key(plaintext)
    key_prefix = plaintext[:PREFIX_DISPLAY_LEN]

    row = db.execute(
        text("""
            INSERT INTO homestock.api_keys (user_id, label, key_hash, key_prefix)
            VALUES (:user_id, :label, :key_hash, :key_prefix)
            RETURNING id, label, key_prefix, created_at, last_used_at
        """),
        {"user_id": user_id, "label": label, "key_hash": key_hash, "key_prefix": key_prefix},
    ).first()
    db.commit()

    return ApiKeyCreated(
        id=row.id,
        label=row.label,
        key_prefix=row.key_prefix,
        created_at=row.created_at,
        last_used_at=row.last_used_at,
        key=plaintext,
    )


def list_api_keys(db: Session, user_id: int) -> list[ApiKeyOut]:
    """List a user's API keys (non-secret columns only), newest first."""
    rows = db.execute(
        text("""
            SELECT id, label, key_prefix, created_at, last_used_at
            FROM homestock.api_keys
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        """),
        {"user_id": user_id},
    ).all()
    return [
        ApiKeyOut(
            id=row.id,
            label=row.label,
            key_prefix=row.key_prefix,
            created_at=row.created_at,
            last_used_at=row.last_used_at,
        )
        for row in rows
    ]


def delete_api_key(db: Session, user_id: int, key_id: int) -> bool:
    """Delete a user's API key. Scoped by user_id so a user can't delete another's key.
    Returns True if a row was deleted, False otherwise."""
    result = db.execute(
        text("DELETE FROM homestock.api_keys WHERE id = :id AND user_id = :user_id"),
        {"id": key_id, "user_id": user_id},
    )
    db.commit()
    return result.rowcount > 0


def resolve_user_by_api_key(db: Session, plaintext: str) -> Optional[dict]:
    """Resolve a plaintext API key to its owning user. Returns a user dict matching the
    shape of get_user_by_username, or None if the key is unknown. Updates last_used_at."""
    key_hash = _hash_key(plaintext)
    row = db.execute(
        text("""
            SELECT u.id, u.username, u.hashed_password, u.oidc_sub, u.oidc_provider,
                   k.id AS key_id
            FROM homestock.api_keys k
            JOIN homestock.users u ON u.id = k.user_id
            WHERE k.key_hash = :key_hash
        """),
        {"key_hash": key_hash},
    ).first()

    if row is None:
        return None

    db.execute(
        text("UPDATE homestock.api_keys SET last_used_at = NOW() WHERE id = :id"),
        {"id": row.key_id},
    )
    db.commit()

    return {
        "id": row.id,
        "username": row.username,
        "hashed_password": row.hashed_password,
        "oidc_sub": row.oidc_sub,
        "oidc_provider": row.oidc_provider,
    }
