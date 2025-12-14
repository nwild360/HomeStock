from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.dependencies.db_session import get_dbsession
from app.dependencies.auth import require_auth

router = APIRouter(tags=["meta"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/healthz")
@limiter.limit("120/minute")  # Allow Docker health checks + monitoring tools
def healthz(request: Request):
    return {"ok": True}


@router.post(
    "/admin/blacklist/cleanup",
    summary="Clean up expired JWT tokens (Admin)",
    description="Manually trigger cleanup of expired tokens from the blacklist. Requires authentication."
)
def cleanup_blacklist(
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_dbsession)
):
    """
    Admin endpoint to manually clean up expired JWT tokens from the blacklist.

    Removes all tokens where expires_at < NOW().
    This helps prevent table bloat and is automatically run on startup.

    Requires valid authentication.
    """
    from app.api.services.blacklist_cleanup import cleanup_expired_tokens

    cleanup_expired_tokens(db)

    return {"message": "Expired tokens cleaned up successfully"}


@router.get(
    "/admin/blacklist/stats",
    summary="Get blacklist statistics (Admin)",
    description="View statistics about the JWT blacklist. Requires authentication."
)
def get_blacklist_stats(
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_dbsession)
):
    """
    Get statistics about the JWT token blacklist.

    Returns:
    - total: Total number of blacklisted tokens
    - expired: Number of expired tokens (can be cleaned up)
    - active: Number of active blacklisted tokens

    Requires valid authentication.
    """
    from app.api.services.blacklist_cleanup import get_blacklist_stats

    stats = get_blacklist_stats(db)

    return {
        "blacklist_stats": stats,
        "message": f"Total: {stats['total']}, Active: {stats['active']}, Expired: {stats['expired']}"
    }
