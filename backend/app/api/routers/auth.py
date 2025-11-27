from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.schemas import Token, UserCreate, UserOut
from app.api.services import auth_service
from app.dependencies.db_session import get_dbsession
from app.dependencies.auth import require_auth

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
    description="Authenticate with username and password to receive a JWT access token (30 min expiry)."
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_dbsession)
):
    """
    OAuth2 compatible token login endpoint.

    Use this endpoint to get an access token for authentication.

    - **username**: Your username
    - **password**: Your password

    Returns a JWT access token that expires in 30 minutes.

    Usage in subsequent requests:
    ```
    Authorization: Bearer <access_token>
    ```
    """
    return auth_service.login_user(db, form_data.username, form_data.password)


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

    Requires valid JWT token in Authorization header.
    """
    return UserOut(
        id=current_user["id"],
        username=current_user["username"]
    )
