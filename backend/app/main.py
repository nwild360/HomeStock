from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routers import meta, items, auth
from app.config import get_settings
from app.init.default_user import initialize_default_user

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - runs on startup and shutdown."""
    # Startup: Initialize default user if needed
    initialize_default_user()
    yield
    # Shutdown: cleanup if needed (none currently)


app = FastAPI(
    title="HomeStock API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

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
