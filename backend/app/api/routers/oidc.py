"""
OIDC router: SSO login redirect, callback, public config, and admin settings.

Endpoints:
  GET  /api/auth/oidc/config    — public: is OIDC enabled? (used by login screen)
  GET  /api/auth/oidc/login     — redirect browser to Keycloak
  GET  /api/auth/oidc/callback  — Keycloak posts back here; issues local JWT
  GET  /api/auth/oidc/settings  — admin: read full OIDC settings
  PUT  /api/auth/oidc/settings  — admin: save OIDC settings
"""
import base64
import secrets
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.api.schemas import OidcConfig, OidcSettings
from app.api.services import oidc_service
from app.dependencies.db_session import get_dbsession
from app.dependencies.auth import require_auth
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/auth/oidc", tags=["oidc"])

OIDC_COOKIE_MAX_AGE = 300          # 5 minutes — state/nonce/verifier cookies
OIDC_COOKIE_SAMESITE = "lax"       # must be lax: cross-origin redirect from Keycloak


# ---------------------------------------------------------------------------
# Public config (used by login screen to decide whether to show SSO button)
# ---------------------------------------------------------------------------

@router.get("/config", response_model=OidcConfig)
def oidc_config(db: Session = Depends(get_dbsession)):
    """Return whether OIDC is enabled and the client_id (no secret exposed)."""
    cfg = oidc_service.get_oidc_settings(db)
    if cfg is None or not cfg.enabled:
        return OidcConfig(enabled=False)
    return OidcConfig(enabled=True, client_id=cfg.client_id)


# ---------------------------------------------------------------------------
# Login: redirect to Keycloak
# ---------------------------------------------------------------------------

@router.get("/login")
def oidc_login(response: Response, db: Session = Depends(get_dbsession)):
    """
    Generate PKCE + state + nonce, store in short-lived httpOnly cookies,
    then redirect the browser to Keycloak's authorization endpoint.
    """
    cfg = oidc_service.get_oidc_settings(db)
    if cfg is None or not cfg.enabled or not cfg.issuer_url or not cfg.client_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OIDC is not configured")

    try:
        discovery = oidc_service.fetch_discovery(cfg.issuer_url)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    auth_endpoint = discovery["authorization_endpoint"]

    # PKCE
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
    code_challenge = oidc_service.pkce_challenge(code_verifier)

    # CSRF + replay protection
    state = secrets.token_hex(32)
    nonce = secrets.token_hex(32)

    from urllib.parse import urlencode
    params = urlencode({
        "client_id": cfg.client_id,
        "redirect_uri": cfg.redirect_uri,
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })
    redirect_url = f"{auth_endpoint}?{params}"

    redirect = RedirectResponse(url=redirect_url, status_code=302)

    cookie_opts = dict(httponly=True, max_age=OIDC_COOKIE_MAX_AGE, samesite=OIDC_COOKIE_SAMESITE, path="/")
    redirect.set_cookie("oidc_state", state, **cookie_opts)
    redirect.set_cookie("oidc_nonce", nonce, **cookie_opts)
    redirect.set_cookie("oidc_code_verifier", code_verifier, **cookie_opts)

    return redirect


# ---------------------------------------------------------------------------
# Callback: exchange code, validate token, provision user, issue local JWT
# ---------------------------------------------------------------------------

@router.get("/callback")
def oidc_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_dbsession),
):
    """
    Keycloak redirects here after user authenticates.
    Validates state (CSRF), exchanges code for tokens (with PKCE),
    validates the id_token, provisions the user, issues a local JWT cookie,
    then redirects to the frontend.
    """
    frontend_url = settings.FRONTEND_URL

    # Keycloak may send error param (e.g. user cancelled)
    if error:
        logger.warning(f"OIDC callback received error from provider: {error}")
        return RedirectResponse(url=f"{frontend_url}?oidc_error={error}", status_code=302)

    if not code or not state:
        return RedirectResponse(url=f"{frontend_url}?oidc_error=missing_params", status_code=302)

    # --- CSRF check ---
    stored_state = request.cookies.get("oidc_state")
    if not stored_state or stored_state != state:
        logger.warning("OIDC callback: state mismatch — possible CSRF attack")
        return RedirectResponse(url=f"{frontend_url}?oidc_error=state_mismatch", status_code=302)

    stored_nonce = request.cookies.get("oidc_nonce")
    code_verifier = request.cookies.get("oidc_code_verifier")
    if not stored_nonce or not code_verifier:
        return RedirectResponse(url=f"{frontend_url}?oidc_error=missing_cookies", status_code=302)

    # --- Load OIDC settings ---
    cfg = oidc_service.get_oidc_settings(db)
    if cfg is None or not cfg.enabled:
        return RedirectResponse(url=f"{frontend_url}?oidc_error=oidc_disabled", status_code=302)

    try:
        discovery = oidc_service.fetch_discovery(cfg.issuer_url)
        tokens = oidc_service.exchange_code_for_tokens(
            token_endpoint=discovery["token_endpoint"],
            code=code,
            redirect_uri=cfg.redirect_uri,
            client_id=cfg.client_id,
            client_secret=cfg.client_secret,
            code_verifier=code_verifier,
        )
        claims = oidc_service.validate_id_token(
            id_token=tokens["id_token"],
            jwks_uri=discovery["jwks_uri"],
            client_id=cfg.client_id,
            issuer_url=discovery["issuer"],  # use discovery doc, not user input — exact string Keycloak puts in iss claim
            nonce=stored_nonce,
        )
    except (RuntimeError, ValueError) as e:
        logger.error(f"OIDC callback failed: {e}")
        return RedirectResponse(url=f"{frontend_url}?oidc_error=auth_failed", status_code=302)

    sub = claims.get("sub")
    preferred_username = claims.get("preferred_username") or claims.get("email") or sub

    user = oidc_service.get_or_create_oidc_user(db, sub=sub, preferred_username=preferred_username, provider="keycloak")
    access_token = oidc_service.create_local_token_for_user(user["username"])

    redirect = RedirectResponse(url=frontend_url, status_code=302)

    # Issue local JWT cookie (same settings as password login)
    redirect.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=1800,
        path="/",
    )

    # Clear OIDC state cookies
    for cookie_name in ("oidc_state", "oidc_nonce", "oidc_code_verifier"):
        redirect.delete_cookie(cookie_name, path="/")

    logger.info(f"OIDC login successful for user '{user['username']}' (sub={sub})")
    return redirect


# ---------------------------------------------------------------------------
# Admin: read/write OIDC settings
# ---------------------------------------------------------------------------

@router.get("/settings", response_model=OidcSettings)
def get_oidc_settings(
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_dbsession),
):
    """Return full OIDC settings including client_secret (authenticated admin only)."""
    cfg = oidc_service.get_oidc_settings(db)
    if cfg is None:
        return OidcSettings(enabled=False)
    return cfg


@router.put("/settings", response_model=OidcSettings)
def update_oidc_settings(
    new_settings: OidcSettings,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_dbsession),
):
    """Save OIDC settings. Takes effect immediately — no restart required."""
    if new_settings.enabled:
        missing = [f for f in ("issuer_url", "client_id", "client_secret", "redirect_uri")
                   if not getattr(new_settings, f)]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Required when enabling OIDC: {', '.join(missing)}",
            )
    oidc_service.save_oidc_settings(db, new_settings)
    return new_settings
