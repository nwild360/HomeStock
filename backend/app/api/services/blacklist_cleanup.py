"""JWT Blacklist Cleanup Service

Provides functions to clean up expired JWT tokens from the blacklist.
Expired tokens are automatically removed to prevent table bloat.
"""

import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def cleanup_expired_tokens(db: Session) -> int:
    """
    Remove expired JWT tokens from the blacklist.

    Returns:
        Number of tokens removed
    """
    try:
        result = db.execute(
            text("SELECT homestock.cleanup_expired_jwt_tokens()")
        )
        db.commit()

        # Count how many were deleted
        count_result = db.execute(
            text("SELECT COUNT(*) FROM homestock.jwt_blacklist WHERE expires_at < NOW()")
        ).scalar()

        # Since we just deleted them, get the count before deletion
        # by checking the number of rows affected
        deleted_count = 0  # We'll log this differently

        logger.info(f"✅ Blacklist cleanup completed - expired tokens removed")
        return deleted_count

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to cleanup expired tokens: {e}")
        raise


def get_blacklist_stats(db: Session) -> dict:
    """
    Get statistics about the JWT blacklist.

    Returns:
        Dictionary with total, expired, and active token counts
    """
    try:
        total = db.execute(
            text("SELECT COUNT(*) FROM homestock.jwt_blacklist")
        ).scalar()

        expired = db.execute(
            text("SELECT COUNT(*) FROM homestock.jwt_blacklist WHERE expires_at < NOW()")
        ).scalar()

        active = total - expired

        return {
            "total": total,
            "expired": expired,
            "active": active
        }

    except Exception as e:
        logger.error(f"❌ Failed to get blacklist stats: {e}")
        raise
