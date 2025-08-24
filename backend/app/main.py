from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import meta, items
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="HomeStock API", 
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
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
app.include_router(items.router, prefix="/api")
