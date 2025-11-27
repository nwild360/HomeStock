from datetime import timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.dependencies.auth import (
    User,
    authenticate_user,
    create_access_token,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.api.schemas import UserCreate, UserOut, Token


def register_user(db: Session, user_data: UserCreate) -> UserOut:
    """
    Register a new user with hashed password.
    Returns UserOut Pydantic model (without password).
    Raises HTTPException on error.
    """
    try:
        # Hash the password
        hashed_password = get_password_hash(user_data.password)

        # Create new user instance
        new_user = User(
            username=user_data.username,
            hashed_password=hashed_password
        )

        # Add to database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Return user without password
        return UserOut(
            id=new_user.id,
            username=new_user.username
        )

    except IntegrityError as e:
        db.rollback()
        if 'unique constraint' in str(e.orig).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user data"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )


def login_user(db: Session, username: str, password: str) -> Token:
    """
    Authenticate user and return JWT access token.
    Returns Token Pydantic model with access_token.
    Raises HTTPException if authentication fails.
    """
    # Authenticate user
    user = authenticate_user(db, username, password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer"
    )
