"""
Default User Initialization for HomeStock

Creates a default admin user on application startup if no users exist.
This is for internal/self-hosted deployments where public registration is disabled.

A secure random password is generated on first startup and displayed ONCE.
Save this password immediately - it cannot be recovered!

The user can change credentials via /api/auth/change-username and
/api/auth/change-password endpoints after first login.
"""

import logging
import secrets
import string
from sqlalchemy import select
from app.dependencies.db_session import DBSession
from app.dependencies.auth import User, get_password_hash

logger = logging.getLogger(__name__)

DEFAULT_USERNAME = "admin"


def generate_secure_password(length: int = 20) -> str:
    """Generate a cryptographically secure random password using safe characters only."""
    # Use safe special chars only (no quotes, angle brackets, etc.)
    safe_special_chars = "!@#$%^&*()_-=+"
    alphabet = string.ascii_letters + string.digits + safe_special_chars

    # Ensure at least one of each type
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice(safe_special_chars),
    ]
    # Fill the rest randomly
    password += [secrets.choice(alphabet) for _ in range(length - 4)]
    # Shuffle to avoid predictable pattern
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


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

        # No users exist - create default user with secure random password
        GENERATED_PASSWORD = generate_secure_password()

        logger.warning("=" * 70)
        logger.warning("⚠️  NO USERS FOUND - Creating default user")
        logger.warning("=" * 70)
        logger.warning(f"Default Username: {DEFAULT_USERNAME}")
        logger.warning(f"Default Password: {GENERATED_PASSWORD}")
        logger.warning("=" * 70)
        logger.warning("⚠️  SAVE THIS PASSWORD NOW - IT WILL NOT BE SHOWN AGAIN!")
        logger.warning("=" * 70)

        # Hash the generated password
        hashed_password = get_password_hash(GENERATED_PASSWORD)

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
