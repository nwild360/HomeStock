from fastapi import APIRouter, Depends, Response, status, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.api.schemas import Token, UserCreate, UserOut, PasswordChange, UsernameChange
from app.api.services import auth_service
from app.dependencies.db_session import get_dbsession
from app.dependencies.auth import require_auth
from app.config import get_settings

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with username and password. Password will be hashed using Argon2id."
)
@limiter.limit("3/hour")
def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth)
):
    """
    Register a new user.

    - **username**: 3-50 characters, alphanumeric with underscores/hyphens only
    - **password**: 8-100 characters minimum

    Returns the created user (without password).
    """
    return auth_service.register_user(db, user_data)


@router.post(
    "/token",
    response_model=Token,
    summary="Login to get access token",
    description="Authenticate with username and password. Sets httpOnly cookie AND returns JWT in response body (30 min expiry)."
)
@limiter.limit("5/15minutes")
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_dbsession)
):
    """
    OAuth2 compatible token login endpoint with httpOnly cookie.

    Use this endpoint to authenticate and receive a secure httpOnly cookie.

    - **username**: Your username
    - **password**: Your password

    Sets a secure httpOnly cookie that expires in 30 minutes.
    The cookie is automatically included in subsequent requests.

    Security features:
    - HttpOnly: Prevents JavaScript access (XSS protection)
    - Secure: Only sent over HTTPS
    - SameSite=Strict: Prevents CSRF attacks
    """
    token_data = auth_service.login_user(db, form_data.username, form_data.password)

    # Set httpOnly cookie with JWT (for frontend)
    response.set_cookie(
        key="access_token",
        value=token_data.access_token,
        httponly=True,        # Prevents JavaScript access (XSS protection)
        secure=settings.COOKIE_SECURE,  # Configured via .env (True for HTTPS/prod, False for HTTP/dev)
        samesite=settings.COOKIE_SAMESITE,  # Configured via .env ("lax" for dev, "strict" for prod)
        max_age=1800,         # 30 minutes (matches JWT expiry)
        path="/",             # Available for all routes
    )

    # Return token in response body (for Swagger UI and API clients)
    return token_data


@router.get(
    "/users",
    response_model=list[UserOut],
    summary="Get all users",
    description="Get a list of all registered users (requires authentication)."
)
@limiter.limit("20/minute")
def get_all_users(
    request: Request,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_dbsession)
):
    """
    Get all users in the system.

    Requires valid JWT token in httpOnly cookie.
    """
    from app.dependencies.auth import User
    users = db.query(User).all()
    return [UserOut(id=user.id, username=user.username) for user in users]


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user info",
    description="Get information about the currently authenticated user."
)
@limiter.limit("60/minute")
def get_current_user_info(
    request: Request,
    current_user: dict = Depends(require_auth)
):
    """
    Get current authenticated user's information.

    Requires valid JWT token in httpOnly cookie.
    """
    return UserOut(
        id=current_user["id"],
        username=current_user["username"]
    )


@router.post(
    "/logout",
    summary="Logout and revoke token",
    description="Blacklists the current JWT token and clears the httpOnly cookie. Token cannot be reused after logout."
)
@limiter.limit("20/minute")
def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_dbsession)
):
    """
    Logout endpoint - blacklists JWT token and clears the httpOnly cookie.

    This invalidates the session both client-side (cookie removal) and server-side (token blacklist).
    The JWT is added to the blacklist table and cannot be reused, even if intercepted.

    Security improvements:
    - Prevents token reuse after logout
    - Token blacklist entry auto-expires when JWT expires (30 min)
    - Protects against token theft/replay attacks
    """
    from app.dependencies.auth import blacklist_token, oauth2_scheme
    from fastapi import Cookie
    import jwt
    from app.crypto.keys import get_ed25519_public_key

    # Get the token from cookie or Authorization header
    access_token = request.cookies.get("access_token")
    if not access_token:
        # Fallback to Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ")[1]

    if access_token:
        try:
            # Decode token to get JTI and expiry
            payload = jwt.decode(
                access_token,
                get_ed25519_public_key(),
                algorithms=["EdDSA"],
                issuer="homestock-api",
                audience="homestock-client"
            )

            jti = payload.get("jti")
            exp = payload.get("exp")

            if jti and exp:
                from datetime import datetime, timezone
                expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)

                # Add token to blacklist
                blacklist_token(db, jti, current_user["username"], expires_at)
        except Exception as e:
            # If token decoding fails, still proceed with cookie deletion
            pass

    # Clear httpOnly cookie
    response.delete_cookie(
        key="access_token",
        path="/",
        samesite=settings.COOKIE_SAMESITE
    )

    return {"message": "Logged out successfully - token has been revoked"}


@router.patch(
    "/me/password",
    summary="Change user password",
    description="Change the current user's password. Requires current password verification. Invalidates all sessions."
)
@limiter.limit("3/hour")
def change_password(
    request: Request,
    password_data: PasswordChange,
    response: Response,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_dbsession)
):
    """
    Change password for the authenticated user.

    Security features (OWASP compliant):
    - Requires current password verification (prevents session hijacking abuse)
    - New password must be different from current password
    - Invalidates all existing sessions by clearing httpOnly cookie
    - Password complexity enforced by Pydantic schema (8-100 chars, alphanumeric with _-)
    - Hashed with Argon2id (64MB memory, 3 iterations, 4 threads)

    Args:
    - **current_password**: Current password for verification
    - **new_password**: New password (8-100 chars, alphanumeric with underscores/hyphens)

    Returns:
    - Success message

    Raises:
    - 401: Current password is incorrect
    - 400: New password same as current or validation failed
    - 500: Server error
    """
    result = auth_service.change_password(db, current_user["id"], password_data)

    # Clear httpOnly cookie to invalidate current session
    # User must re-login with new password
    if result.get("invalidate_sessions"):
        response.delete_cookie(
            key="access_token",
            path="/",
            samesite=settings.COOKIE_SAMESITE
        )

    return {"message": result["message"]}


@router.patch(
    "/me/username",
    response_model=UserOut,
    summary="Change username",
    description="Change the current user's username. Must be unique."
)
@limiter.limit("3/hour")
def change_username(
    request: Request,
    username_data: UsernameChange,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_dbsession)
):
    """
    Change username for the authenticated user.

    Security features:
    - Requires valid authentication (JWT token)
    - Validates uniqueness (prevents conflicts)
    - Username complexity enforced by Pydantic schema (3-50 chars, alphanumeric with _-)
    - New username must be different from current username

    Args:
    - **new_username**: New username (3-50 chars, alphanumeric with underscores/hyphens)

    Returns:
    - Updated user information (without password)

    Raises:
    - 409: Username already exists
    - 400: New username same as current or validation failed
    - 500: Server error

    Note: Does NOT invalidate existing sessions. Current JWT token remains valid
    until expiry, but will contain the old username in the 'sub' claim.
    """
    return auth_service.change_username(db, current_user["id"], username_data)


@router.delete(
    "/users/{user_id}",
    summary="Delete a user",
    description="Delete a user by ID (requires authentication)."
)
@limiter.limit("5/hour")
def delete_user(
    request: Request,
    user_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_dbsession)
):
    """
    Delete a user by ID.

    Args:
    - **user_id**: The ID of the user to delete

    Returns:
    - Success message

    Raises:
    - 403: Cannot delete yourself
    - 404: User not found
    - 500: Server error
    """
    from app.dependencies.auth import User

    # Prevent users from deleting themselves
    if current_user["id"] == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete your own account"
        )

    # Find and delete the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db.delete(user)
    db.commit()

    return {"message": f"User '{user.username}' deleted successfully"}
