from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.schemas import Token, UserCreate, UserOut
from app.api.services import auth_service
from app.dependencies.db_session import get_dbsession
from app.dependencies.auth import require_auth
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with username and password. Password will be hashed using Argon2id."
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_dbsession)
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
def login(
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
    "/me",
    response_model=UserOut,
    summary="Get current user info",
    description="Get information about the currently authenticated user."
)
def get_current_user_info(
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
    summary="Logout and clear session",
    description="Clears the httpOnly cookie to log out the user."
)
def logout(response: Response):
    """
    Logout endpoint - clears the httpOnly cookie.

    This invalidates the session on the client side by removing the cookie.
    The JWT itself remains valid until expiry, but the browser won't send it anymore.
    """
    response.delete_cookie(
        key="access_token",
        path="/",
        samesite="strict"
    )

    return {"message": "Logged out successfully"}
