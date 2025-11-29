"""
Default User Initialization for HomeStock

Creates a default admin user on application startup if no users exist.
This is for internal/self-hosted deployments where public registration is disabled.

Default credentials (CHANGE THESE IMMEDIATELY AFTER FIRST LOGIN):
- Username: admin
- Password: homestock

The user should change these via the /api/auth/change-username and
/api/auth/change-password endpoints after first login.
"""

import logging
from sqlalchemy import select
from app.dependencies.db_session import DBSession
from app.dependencies.auth import User, get_password_hash

logger = logging.getLogger(__name__)

DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "homestock"


def initialize_default_user():
    """
    Create default user if no users exist in the database.

    This runs on application startup. If the users table is empty,
    it creates an admin user with default credentials.
    """
    logger.info("Checking if default user initialization is needed...")

    db = DBSession()
    try:
        # Check if any users exist
        result = db.execute(select(User)).first()

        if result is not None:
            logger.info("✓ Users already exist in database - skipping default user creation")
            return

        # No users exist - create default user
        logger.warning("=" * 70)
        logger.warning("⚠️  NO USERS FOUND - Creating default user")
        logger.warning("=" * 70)
        logger.warning(f"Default Username: {DEFAULT_USERNAME}")
        logger.warning(f"Default Password: {DEFAULT_PASSWORD}")
        logger.warning("=" * 70)
        logger.warning("⚠️  CHANGE THESE CREDENTIALS IMMEDIATELY AFTER FIRST LOGIN!")
        logger.warning("=" * 70)

        # Hash the default password
        hashed_password = get_password_hash(DEFAULT_PASSWORD)

        # Create default user
        default_user = User(
            username=DEFAULT_USERNAME,
            hashed_password=hashed_password
        )

        db.add(default_user)
        db.commit()
        db.refresh(default_user)

        logger.info(f"✅ Default user created successfully (user_id={default_user.id})")
        logger.warning("⚠️  Remember to change the default credentials via /api/auth/change-password")

    except Exception as e:
        logger.error(f"❌ Failed to create default user: {e}")
        logger.warning("⚠️  Application will continue startup. You can:")
        logger.warning("   1. Wait for DB to be ready and restart the backend")
        logger.warning("   2. Register a user manually via /api/auth/register")
        db.rollback()
        # Don't raise - allow app to start even if default user creation fails
    finally:
        db.close()
