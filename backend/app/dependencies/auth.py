from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from passlib.context import CryptContext
from sqlalchemy import BigInteger, Column, String, select
from sqlalchemy.orm import declarative_base, Session
from app.config import get_settings
from app.dependencies.db_session import get_dbsession
from app.crypto.keys import get_ed25519_private_key, get_ed25519_public_key

settings = get_settings()
logger = logging.getLogger(__name__)

# SQLAlchemy ORM Model for User
Base = declarative_base()

class User(Base):
    """SQLAlchemy ORM model for users table."""
    __tablename__ = "users"
    __table_args__ = {"schema": "homestock"}

    id = Column(BigInteger, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

# Password hashing context using Argon2id
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,         # 3 iterations
    argon2__parallelism=4        # 4 parallel threads
)

# OAuth2 scheme - token obtained from /api/auth/token endpoint
# auto_error=False allows cookies to be used as fallback
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

# JWT Settings - Ed25519
ALGORITHM = "EdDSA"  # Ed25519 algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using Argon2id."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using Argon2id."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token signed with Ed25519.

    Ed25519 produces tiny signatures (64 bytes) that fit easily in cookies.
    Much smaller than RSA (256 bytes) or Dilithium3 (3,293 bytes).
    """
    username = data.get("sub", "unknown")
    logger.debug(f"Creating Ed25519 JWT for user: {username}")

    # Prepare payload
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,
        "iss": "homestock-api",
        "aud": "homestock-client"
    })

    # Sign with Ed25519 using PyJWT
    encoded_jwt = jwt.encode(
        to_encode,
        get_ed25519_private_key(),
        algorithm=ALGORITHM
    )

    logger.info(f"✅ Ed25519 JWT created for '{username}' | Token size: {len(encoded_jwt)} bytes | Expires: {to_encode['exp']}")

    return encoded_jwt


def get_user_by_username(db: Session, username: str) -> Optional[dict]:
    """Fetch user by username from database using SQLAlchemy ORM."""
    user = db.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()

    if user:
        return {
            "id": user.id,
            "username": user.username,
            "hashed_password": user.hashed_password
        }
    return None


def authenticate_user(db: Session, username: str, password: str) -> Optional[dict]:
    """Authenticate user with username and password."""
    logger.debug(f"Authentication attempt for user: {username}")

    user = get_user_by_username(db, username)
    if not user:
        logger.warning(f"❌ Authentication failed: User '{username}' not found")
        return None

    if not verify_password(password, user["hashed_password"]):
        logger.warning(f"❌ Authentication failed: Invalid password for user '{username}'")
        return None

    logger.info(f"✅ User '{username}' authenticated successfully via password")
    return user


async def get_current_user(
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_dbsession)
) -> dict:
    """
    Dependency to get current authenticated user from Ed25519 JWT token.

    Supports TWO authentication methods:
    1. httpOnly cookie (for frontend) - Primary method
    2. Authorization Bearer header (for Swagger UI, API testing) - Fallback

    Verifies Ed25519 signature using PyJWT.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try cookie first (frontend), then Authorization header (Swagger/API)
    token = access_token or authorization

    if not token:
        logger.warning("❌ No access_token cookie or Authorization header found in request")
        raise credentials_exception

    try:
        # Decode and verify JWT with Ed25519
        logger.debug("Verifying Ed25519 signature...")
        payload = jwt.decode(
            token,
            get_ed25519_public_key(),
            algorithms=[ALGORITHM],
            issuer="homestock-api",
            audience="homestock-client"
        )
        logger.debug("✓ Ed25519 signature verified")

        # Extract username
        username: str = payload.get("sub")
        if username is None:
            logger.warning("❌ Token missing 'sub' claim (username)")
            raise credentials_exception

        logger.info(f"✅ Ed25519 signature verification SUCCESS for user: {username}")

    except jwt.ExpiredSignatureError:
        logger.error("❌ JWT token has expired")
        raise credentials_exception
    except jwt.InvalidTokenError as e:
        logger.error(f"❌ JWT token validation failed: {type(e).__name__}: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"❌ Unexpected error during token verification: {type(e).__name__}: {e}")
        raise credentials_exception

    # Look up user in database
    user = get_user_by_username(db, username)
    if user is None:
        logger.warning(f"❌ User '{username}' not found in database (token valid but user deleted?)")
        raise credentials_exception

    logger.info(f"✅ User '{username}' authenticated successfully (user_id={user['id']})")
    return user


# Dependency for protected routes
async def require_auth(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency for requiring authentication on routes."""
    return current_user
