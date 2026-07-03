from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.routing import Route
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter
from app.api.routers import meta, items, auth, data, oidc, receipt, backups, api_keys, mcp as mcp_router
from app.config import get_settings
from app.init.default_user import initialize_default_user
from app.mcp_server.auth import McpAuthMiddleware
from app.mcp_server.server import mcp as mcp_instance

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - runs on startup and shutdown."""
    # Startup: Initialize default user if needed
    initialize_default_user()

    # Startup: Clean up expired JWT tokens from blacklist
    from app.dependencies.db_session import get_dbsession
    from app.api.services.blacklist_cleanup import cleanup_expired_tokens
    import logging

    logger = logging.getLogger(__name__)
    db = next(get_dbsession())
    try:
        cleanup_expired_tokens(db)
        logger.info("✅ Startup: Expired JWT tokens cleaned from blacklist")
    except Exception as e:
        logger.warning(f"⚠️ Startup: Failed to cleanup blacklist: {e}")
    finally:
        db.close()

    # MCP: mounted sub-app lifespans don't run automatically; the session
    # manager task group must be running for /mcp to serve requests.
    async with mcp_instance.session_manager.run():
        yield
    # Shutdown: cleanup if needed (none currently)


# Conditionally disable API docs in production
docs_url = "/docs" if settings.ENVIRONMENT != "production" else None
redoc_url = "/redoc" if settings.ENVIRONMENT != "production" else None
openapi_url = "/openapi.json" if settings.ENVIRONMENT != "production" else None

app = FastAPI(
    title="HomeStock API",
    version="1.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Cookie"],
    max_age=600  # Cache preflight requests for 10 minutes
)

# Include routers with prefix
app.include_router(meta.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(api_keys.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(data.router, prefix="/api")
app.include_router(oidc.router, prefix="/api")
app.include_router(receipt.router, prefix="/api")
app.include_router(backups.router, prefix="/api")
app.include_router(mcp_router.router, prefix="/api")
app.include_router(mcp_router.well_known_router)  # /.well-known/oauth-protected-resource

# MCP protocol endpoint (Streamable HTTP). An exact Route (not a Mount) so
# POST /mcp is served directly instead of 307-redirecting to /mcp/, which
# some MCP clients won't follow. Registered at module level so
# streamable_http_app() creates the session manager before the lifespan
# accesses it. Auth + enabled-toggle enforced by McpAuthMiddleware.
app.router.routes.append(
    Route("/mcp", McpAuthMiddleware(mcp_instance.streamable_http_app()), methods=["GET", "POST", "DELETE"])
)
