"""
OIDC service: discovery, token exchange, id_token validation, user provisioning.

Uses only stdlib HTTP (urllib) + PyJWT's built-in PyJWKClient — no extra deps.
"""
import hashlib
import json
import logging
import re
import urllib.request
import urllib.parse
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, text
import jwt
from jwt import PyJWKClient
from app.dependencies.auth import User, create_access_token
from app.api.schemas import OidcSettings
from datetime import timedelta
from app.dependencies.auth import ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_oidc_settings(db: Session) -> Optional[OidcSettings]:
    """Read OIDC settings from DB row id=1. Returns None if table is empty."""
    row = db.execute(
        text("SELECT enabled, issuer_url, client_id, client_secret, redirect_uri FROM homestock.oidc_settings WHERE id = 1")
    ).first()
    if row is None:
        return None
    return OidcSettings(
        enabled=row.enabled,
        issuer_url=row.issuer_url,
        client_id=row.client_id,
        client_secret=row.client_secret,
        redirect_uri=row.redirect_uri,
    )


def save_oidc_settings(db: Session, settings: OidcSettings) -> None:
    """Upsert OIDC settings into row id=1."""
    db.execute(
        text("""
            UPDATE homestock.oidc_settings
               SET enabled      = :enabled,
                   issuer_url   = :issuer_url,
                   client_id    = :client_id,
                   client_secret = :client_secret,
                   redirect_uri  = :redirect_uri,
                   updated_at   = NOW()
             WHERE id = 1
        """),
        {
            "enabled": settings.enabled,
            "issuer_url": settings.issuer_url,
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "redirect_uri": settings.redirect_uri,
        }
    )
    db.commit()


# ---------------------------------------------------------------------------
# OIDC discovery
# ---------------------------------------------------------------------------

def fetch_discovery(issuer_url: str) -> dict:
    """Fetch OpenID Connect discovery document from Keycloak."""
    url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # nosec — user-configured issuer
            return json.loads(resp.read())
    except Exception as e:
        logger.error(f"Failed to fetch OIDC discovery from {url}: {e}")
        raise RuntimeError(f"Cannot reach OIDC issuer: {e}") from e


# ---------------------------------------------------------------------------
# Token exchange
# ---------------------------------------------------------------------------

def exchange_code_for_tokens(
    token_endpoint: str,
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
    code_verifier: str,
) -> dict:
    """POST to Keycloak token endpoint, return token response dict."""
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
        "code_verifier": code_verifier,
    }).encode()

    req = urllib.request.Request(
        token_endpoint,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec — user-configured endpoint
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode(errors="replace")
        logger.error(f"Token exchange failed ({e.code}): {error_body}")
        raise RuntimeError(f"Token exchange failed: {e.code}") from e
    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        raise RuntimeError(f"Token exchange error: {e}") from e


# ---------------------------------------------------------------------------
# id_token validation
# ---------------------------------------------------------------------------

def validate_id_token(
    id_token: str,
    jwks_uri: str,
    client_id: str,
    issuer_url: str,
    nonce: str,
) -> dict:
    """
    Validate Keycloak id_token using JWKS.

    PyJWKClient fetches and caches Keycloak's public keys automatically.
    Checks: signature, expiry, issuer, audience, nonce.
    """
    try:
        jwks_client = PyJWKClient(jwks_uri)
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)

        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
            audience=client_id,
            issuer=issuer_url,
        )
    except jwt.ExpiredSignatureError:
        raise ValueError("id_token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"id_token validation failed: {e}") from e

    # PyJWT does not check nonce — do it manually
    if claims.get("nonce") != nonce:
        raise ValueError("Nonce mismatch — possible replay attack")

    return claims


# ---------------------------------------------------------------------------
# Username sanitisation
# ---------------------------------------------------------------------------

def _sanitize_username(raw: str) -> str:
    """
    Convert a Keycloak preferred_username to one that satisfies the DB constraint:
    3-50 chars, alphanumeric + underscore + hyphen only.
    """
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", raw)
    sanitized = sanitized[:45]          # leave room for collision suffix
    if len(sanitized) < 3:
        sanitized = sanitized.ljust(3, "_")
    return sanitized


def _unique_username(db: Session, base: str) -> str:
    """Return base if available, otherwise base_2, base_3, …"""
    candidate = base
    suffix = 2
    while True:
        exists = db.execute(
            select(User).where(User.username == candidate)
        ).scalar_one_or_none()
        if exists is None:
            return candidate
        candidate = f"{base}_{suffix}"
        suffix += 1


# ---------------------------------------------------------------------------
# JIT user provisioning
# ---------------------------------------------------------------------------

def get_or_create_oidc_user(db: Session, sub: str, preferred_username: str, provider: str) -> dict:
    """
    Look up a user by oidc_sub.  If none found, create a new local user row.
    Returns a user dict compatible with get_current_user output.
    """
    user = db.execute(
        select(User).where(User.oidc_sub == sub)
    ).scalar_one_or_none()

    if user is None:
        username = _unique_username(db, _sanitize_username(preferred_username))
        logger.info(f"JIT provisioning OIDC user: sub={sub}, username={username}, provider={provider}")
        user = User(
            username=username,
            hashed_password=None,
            oidc_sub=sub,
            oidc_provider=provider,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "hashed_password": user.hashed_password,
        "oidc_sub": user.oidc_sub,
        "oidc_provider": user.oidc_provider,
    }


# ---------------------------------------------------------------------------
# Issue a local JWT for an OIDC-authenticated user
# ---------------------------------------------------------------------------

def create_local_token_for_user(username: str) -> str:
    """Issue a HomeStock Ed25519 JWT after successful OIDC authentication."""
    return create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


# ---------------------------------------------------------------------------
# PKCE helpers
# ---------------------------------------------------------------------------

def pkce_challenge(verifier: str) -> str:
    """Compute S256 code_challenge from code_verifier."""
    digest = hashlib.sha256(verifier.encode()).digest()
    import base64
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")
