from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from app.config import get_settings

settings = get_settings()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def require_auth_api_key(api_key: str = Security(api_key_header)):
    """Dependency for requiring and validating API key."""
    if api_key != settings.API_KEY:  # You'll need to add API_KEY to your Settings class
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key