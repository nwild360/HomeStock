from datetime import timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.dependencies.auth import (
    User,
    authenticate_user,
    create_access_token,
    get_password_hash,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.api.schemas import UserCreate, UserOut, Token, PasswordChange, UsernameChange


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


def change_password(db: Session, user_id: int, password_data: PasswordChange) -> dict:
    """
    Change user password with current password verification.

    Security features:
    - Requires current password verification (prevents session hijacking abuse)
    - Hashes new password with Argon2id
    - Returns success flag for session invalidation

    Args:
        db: Database session
        user_id: ID of authenticated user
        password_data: Current and new password

    Returns:
        dict with success message

    Raises:
        HTTPException: If current password is incorrect or update fails
    """
    try:
        # Fetch user from database
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password (OWASP requirement)
        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )

        # Check if new password is different from current
        if verify_password(password_data.new_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )

        # Hash new password
        new_hashed_password = get_password_hash(password_data.new_password)

        # Update password in database
        user.hashed_password = new_hashed_password
        db.commit()

        return {
            "message": "Password changed successfully",
            "invalidate_sessions": True  # Signal to router to clear cookies
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error changing password"
        )


def change_username(db: Session, user_id: int, username_data: UsernameChange) -> UserOut:
    """
    Change username with uniqueness validation.

    Security features:
    - Validates uniqueness (prevents conflicts)
    - Updates user record
    - Returns updated user info

    Args:
        db: Database session
        user_id: ID of authenticated user
        username_data: New username

    Returns:
        UserOut with updated username

    Raises:
        HTTPException: If username already exists or update fails
    """
    try:
        # Fetch user from database
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if username is same as current
        if user.username == username_data.new_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New username must be different from current username"
            )

        # Update username
        user.username = username_data.new_username
        db.commit()
        db.refresh(user)

        return UserOut(
            id=user.id,
            username=user.username
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
            detail="Invalid username"
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error changing username"
        )
