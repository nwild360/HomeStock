"""
OAuth 2.1 access-token verification for the MCP endpoint.

The MCP server acts as an OAuth resource server (per the MCP authorization
spec): tokens are minted by the household's Keycloak (the same issuer
configured in SSO/OIDC settings) and validated here via OAuth 2.0 Token
Introspection (RFC 7662), so validation is delegated to Keycloak rather than
hand-rolled. Audience matching reuses the MCP SDK's auth utilities.

All configuration is read from the DB per request (oidc_settings for the
issuer + introspection client, mcp_settings for the audience/scope), so
settings changes apply live without a backend restart.
"""
import hashlib
import logging
import time
from typing import Optional

import httpx
from sqlalchemy.orm import Session
from mcp.shared.auth_utils import check_resource_allowed, resource_url_from_server_url

from app.api.services import mcp_settings_service, oidc_service

logger = logging.getLogger(__name__)

# issuer_url -> (expires_monotonic, introspection_endpoint)
_discovery_cache: dict[str, tuple[float, str]] = {}
_DISCOVERY_TTL = 3600.0

# sha256(token) -> (expires_monotonic, user dict)
_token_cache: dict[str, tuple[float, dict]] = {}
_TOKEN_CACHE_TTL = 60.0
_TOKEN_CACHE_MAX = 256


async def _introspection_endpoint(issuer_url: str) -> str:
    """Resolve the introspection endpoint from OIDC discovery (cached)."""
    now = time.monotonic()
    cached = _discovery_cache.get(issuer_url)
    if cached and cached[0] > now:
        return cached[1]
    url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            endpoint = resp.json().get("introspection_endpoint")
    except Exception as e:
        logger.warning("OIDC discovery failed (%s); using Keycloak default path", e)
        endpoint = None
    if not endpoint:
        endpoint = f"{issuer_url.rstrip('/')}/protocol/openid-connect/token/introspect"
    _discovery_cache[issuer_url] = (now + _DISCOVERY_TTL, endpoint)
    return endpoint


def _cache_get(token: str) -> Optional[dict]:
    key = hashlib.sha256(token.encode()).hexdigest()
    entry = _token_cache.get(key)
    if entry and entry[0] > time.monotonic():
        return entry[1]
    _token_cache.pop(key, None)
    return None


def _cache_put(token: str, user: dict, token_exp: Optional[int]) -> None:
    ttl = _TOKEN_CACHE_TTL
    if token_exp:
        ttl = max(0.0, min(ttl, token_exp - time.time()))
    if ttl <= 0:
        return
    if len(_token_cache) >= _TOKEN_CACHE_MAX:
        now = time.monotonic()
        for k in [k for k, v in _token_cache.items() if v[0] <= now]:
            _token_cache.pop(k, None)
        if len(_token_cache) >= _TOKEN_CACHE_MAX:
            _token_cache.clear()
    _token_cache[hashlib.sha256(token.encode()).hexdigest()] = (time.monotonic() + ttl, user)


async def verify_oauth_token(db: Session, token: str) -> Optional[dict]:
    """
    Validate an OAuth access token via Keycloak introspection and map it to a
    HomeStock user. Returns the user dict, or None if the token is invalid.
    """
    oidc = oidc_service.get_oidc_settings(db)
    if not (oidc and oidc.enabled and oidc.issuer_url and oidc.client_id):
        logger.info("MCP OAuth rejected: OIDC is not configured")
        return None
    cfg = mcp_settings_service.get_mcp_settings(db)
    if cfg is None or not cfg.server_url:
        logger.info("MCP OAuth rejected: no server_url configured (required as token audience)")
        return None

    cached = _cache_get(token)
    if cached is not None:
        return cached

    endpoint = await _introspection_endpoint(oidc.issuer_url)
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            resp = await client.post(
                endpoint,
                data={
                    "token": token,
                    "client_id": oidc.client_id,
                    "client_secret": oidc.client_secret or "",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except Exception as e:
        logger.error("MCP token introspection request failed: %s", e)
        return None
    if resp.status_code != 200:
        logger.error("MCP token introspection returned %s", resp.status_code)
        return None

    data = resp.json()
    if not data.get("active", False):
        logger.info("MCP OAuth rejected: inactive token")
        return None

    # Audience must cover our resource URL (blocks token passthrough)
    resource_url = str(resource_url_from_server_url(cfg.server_url))
    aud = data.get("aud")
    audiences = aud if isinstance(aud, list) else [aud] if isinstance(aud, str) else []
    if not any(check_resource_allowed(requested_resource=resource_url, configured_resource=a) for a in audiences):
        logger.info("MCP OAuth rejected: audience %s does not cover %s", audiences, resource_url)
        return None

    if cfg.required_scope:
        scopes = (data.get("scope") or "").split()
        if cfg.required_scope not in scopes:
            logger.info("MCP OAuth rejected: missing required scope %s", cfg.required_scope)
            return None

    sub = data.get("sub")
    if not sub:
        logger.info("MCP OAuth rejected: no sub claim")
        return None
    preferred_username = data.get("preferred_username") or data.get("username") or sub
    user = oidc_service.get_or_create_oidc_user(db, sub, preferred_username, provider=oidc.issuer_url)

    _cache_put(token, user, data.get("exp"))
    return user
