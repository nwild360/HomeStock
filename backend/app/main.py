from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.api.routers import meta, items, auth, data
from app.config import get_settings
from app.init.default_user import initialize_default_user

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


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
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600  # Cache preflight requests for 10 minutes
)

# Include routers with prefix
app.include_router(meta.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(data.router, prefix="/api")
