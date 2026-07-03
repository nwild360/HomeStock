"""
ASGI middleware guarding the mounted MCP protocol endpoint.

Per request: checks the mcp_settings.enabled flag, authenticates the caller
(OAuth access token via Keycloak introspection, or an hs_live_ API key when
allow_api_keys is on), and stashes the resolved user in a contextvar for
tool handlers. Runs outside FastAPI routing, so it cannot use Depends().
"""
import json
import logging

from app.api.services import mcp_settings_service
from app.api.services.api_keys_service import resolve_user_by_api_key
from app.dependencies.db_session import DBSession
from app.mcp_server.context import current_mcp_user
from app.mcp_server.oauth import verify_oauth_token

logger = logging.getLogger(__name__)

API_KEY_PREFIX = "hs_live_"


class McpAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Registered as an exact Route at /mcp, so the inner MCP app (whose
        # single endpoint lives at "/") sees the full external path; rewrite
        # it so the inner route matches.
        scope["path"] = "/"

        # Sync DB calls block the loop briefly; queries here are single-row
        # lookups, consistent with the rest of the app's sync SQLAlchemy use.
        db = DBSession()
        try:
            if not mcp_settings_service.is_mcp_enabled(db):
                return await self._json_error(scope, send, 404, "MCP server is not enabled")

            api_key, bearer = self._extract_credentials(scope)
            user = None
            if api_key is not None or (bearer or "").startswith(API_KEY_PREFIX):
                key = api_key if api_key is not None else bearer
                cfg = mcp_settings_service.get_mcp_settings(db)
                if not (cfg and cfg.allow_api_keys):
                    return await self._json_error(
                        scope, send, 401, "API key auth is disabled for the MCP server", challenge=True
                    )
                user = resolve_user_by_api_key(db, key)
            elif bearer:
                user = await verify_oauth_token(db, bearer)
            else:
                return await self._json_error(scope, send, 401, "Missing credentials", challenge=True)

            if user is None:
                return await self._json_error(scope, send, 401, "Invalid credentials", challenge=True)
        finally:
            db.close()

        token = current_mcp_user.set(user)
        try:
            await self.app(scope, receive, send)
        finally:
            current_mcp_user.reset(token)

    @staticmethod
    def _extract_credentials(scope) -> tuple[str | None, str | None]:
        """Return (x_api_key, bearer_token) from the request headers."""
        x_api_key = None
        bearer = None
        for name, value in scope.get("headers", []):
            if name == b"x-api-key":
                x_api_key = value.decode("latin-1").strip()
            elif name == b"authorization":
                auth = value.decode("latin-1").strip()
                if auth.lower().startswith("bearer "):
                    bearer = auth[7:].strip()
        return x_api_key, bearer

    async def _json_error(self, scope, send, status_code: int, detail: str, challenge: bool = False):
        body = json.dumps({"detail": detail}).encode()
        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
        ]
        if challenge:
            metadata_url = f"{self._request_origin(scope)}/.well-known/oauth-protected-resource"
            headers.append((
                b"www-authenticate",
                f'Bearer realm="mcp", resource_metadata="{metadata_url}"'.encode(),
            ))
        await send({"type": "http.response.start", "status": status_code, "headers": headers})
        await send({"type": "http.response.body", "body": body})

    @staticmethod
    def _request_origin(scope) -> str:
        """Best-effort external origin, honoring reverse-proxy headers."""
        headers = {name: value.decode("latin-1") for name, value in scope.get("headers", [])}
        scheme = headers.get(b"x-forwarded-proto") or scope.get("scheme", "http")
        host = headers.get(b"host", "localhost")
        return f"{scheme}://{host}"
