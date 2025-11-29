from datetime import datetime, timedelta, timezone
from typing import Optional
import base64
import json
import logging
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import BigInteger, Column, String, select
from sqlalchemy.orm import declarative_base, Session
from app.config import get_settings
from app.dependencies.db_session import get_dbsession
from app.crypto.keys import (
    get_rsa_private_key,
    get_rsa_public_key,
    dilithium_sign,
    dilithium_verify
)

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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# JWT Settings - Hybrid Cryptography
ALGORITHM = "RS256"  # Primary algorithm (RSA asymmetric)
PQC_ALGORITHM = "Dilithium3"  # Post-quantum algorithm (FIPS 204)
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using Argon2id."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using Argon2id."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a hybrid JWT access token with both RS256 and Dilithium3 signatures.

    The token structure includes:
    - Primary signature: RS256 (for compatibility)
    - Secondary signature: Dilithium3 (for quantum resistance)

    The Dilithium signature is embedded in the JWT header as a custom claim.
    """
    username = data.get("sub", "unknown")
    logger.debug(f"Creating hybrid JWT for user: {username}")

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

    # First, create a basic JWT WITHOUT the PQC signature using python-jose
    # This ensures we sign the exact same encoding that jose creates
    basic_jwt = jwt.encode(
        to_encode,
        get_rsa_private_key(),
        algorithm=ALGORITHM
    )

    # Split the JWT to get the actual header.payload that jose created
    token_parts = basic_jwt.split('.')
    if len(token_parts) != 3:
        raise ValueError("Invalid JWT structure")

    # The message that was signed by jose (header.payload)
    # This is what we'll also sign with Dilithium
    message = f"{token_parts[0]}.{token_parts[1]}"

    # Sign with Dilithium3 (post-quantum)
    dilithium_signature = dilithium_sign(message.encode())
    dilithium_sig_b64 = base64.urlsafe_b64encode(dilithium_signature).decode().rstrip('=')

    # Now create the final JWT with the PQC signature in the header
    header_with_pqc = {
        "alg": ALGORITHM,
        "typ": "JWT",
        "pqc": {
            "alg": PQC_ALGORITHM,
            "sig": dilithium_sig_b64
        }
    }

    # Sign with RS256 using python-jose (creates final JWT)
    encoded_jwt = jwt.encode(
        to_encode,
        get_rsa_private_key(),
        algorithm=ALGORITHM,
        headers=header_with_pqc
    )

    logger.info(f"✅ Hybrid JWT created for '{username}' | RS256 + {PQC_ALGORITHM} | Token size: {len(encoded_jwt)} bytes | Expires: {to_encode['exp']}")

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
    db: Session = Depends(get_dbsession)
) -> dict:
    """
    Dependency to get current authenticated user from hybrid JWT token in httpOnly cookie.

    Verifies BOTH signatures:
    1. RS256 signature (classical security)
    2. Dilithium3 signature (post-quantum security)

    If either signature fails, the token is rejected.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Check if token exists in cookie
    if not access_token:
        logger.warning("❌ No access_token cookie found in request")
        raise credentials_exception

    # Use the cookie value as the token
    token = access_token

    try:
        # Decode the token header without verification first (to get PQC signature)
        unverified_header = jwt.get_unverified_header(token)

        # Verify RS256 signature with python-jose
        logger.debug("Verifying RS256 signature...")
        try:
            payload = jwt.decode(
                token,
                get_rsa_public_key(),
                algorithms=[ALGORITHM],
                issuer="homestock-api",
                audience="homestock-client"
            )
            logger.debug("✓ RS256 signature verified")
        except JWTError as e:
            logger.error(f"❌ RS256 signature verification FAILED: {type(e).__name__}: {e}")
            raise credentials_exception

        # Extract username
        username: str = payload.get("sub")
        if username is None:
            logger.warning("❌ Token missing 'sub' claim (username)")
            raise credentials_exception

        # Verify Dilithium3 signature (if present)
        logger.debug("Verifying Dilithium3 (PQC) signature...")
        if "pqc" in unverified_header:
            pqc_data = unverified_header["pqc"]

            if pqc_data.get("alg") != PQC_ALGORITHM:
                logger.error(f"❌ Invalid PQC algorithm in header: {pqc_data.get('alg')} (expected {PQC_ALGORITHM})")
                raise credentials_exception

            # Extract the Dilithium signature
            dilithium_sig_b64 = pqc_data.get("sig")
            if not dilithium_sig_b64:
                logger.error("❌ PQC signature field exists but is empty")
                raise credentials_exception

            # Decode the signature
            try:
                # Add padding if needed
                padding = 4 - (len(dilithium_sig_b64) % 4)
                if padding != 4:
                    dilithium_sig_b64 += '=' * padding

                dilithium_signature = base64.urlsafe_b64decode(dilithium_sig_b64)
                logger.debug(f"Dilithium signature decoded: {len(dilithium_signature)} bytes")
            except Exception as e:
                logger.error(f"❌ Failed to decode Dilithium signature from base64: {e}")
                raise credentials_exception

            # Extract the actual token parts (header.payload.signature)
            token_parts = token.split('.')
            if len(token_parts) != 3:
                logger.error(f"❌ Invalid token format: expected 3 parts, got {len(token_parts)}")
                raise credentials_exception

            # The Dilithium signature was created against the jose-encoded header.payload
            # We need to reconstruct that same message
            # The current token has header WITH pqc, but the signature was created with header WITHOUT pqc
            # We need to decode the payload and re-encode it with a basic header

            # Decode the payload
            try:
                # Add padding if needed for base64 decoding
                payload_b64 = token_parts[1]
                padding = 4 - (len(payload_b64) % 4)
                if padding != 4:
                    payload_b64 += '=' * padding
                payload_bytes = base64.urlsafe_b64decode(payload_b64)
                payload_data = json.loads(payload_bytes)
            except Exception as e:
                logger.error(f"❌ Failed to decode payload: {e}")
                raise credentials_exception

            # Recreate a basic JWT to get the exact header.payload that was signed
            basic_jwt = jwt.encode(
                payload_data,
                get_rsa_private_key(),
                algorithm=ALGORITHM
            )
            basic_parts = basic_jwt.split('.')

            # The message that was signed with Dilithium (header.payload from basic JWT)
            message = f"{basic_parts[0]}.{basic_parts[1]}"

            # Verify Dilithium signature
            if not dilithium_verify(message.encode(), dilithium_signature):
                logger.error("❌ Dilithium3 signature verification FAILED")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Post-quantum signature verification failed",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            logger.debug("✓ Dilithium3 signature verified")
            logger.info("✅ Hybrid signature verification SUCCESS (RS256 ✓ + Dilithium3 ✓)")
        else:
            logger.error("❌ Token missing PQC signature field in header - rejecting")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing post-quantum signature",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except HTTPException:
        # Re-raise HTTPExceptions (they already have proper logging above)
        raise
    except Exception as e:
        # Catch any other unexpected errors
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
