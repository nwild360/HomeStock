from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.api.schemas import ApiKeyOut, ApiKeyCreate, ApiKeyCreated
from app.api.services import api_keys_service
from app.dependencies.db_session import get_dbsession
from app.dependencies.auth import require_auth

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth/keys", tags=["api-keys"])


# GET /auth/keys
@router.get(
    "",
    response_model=List[ApiKeyOut],
    summary="List the current user's API keys",
)
@limiter.limit("60/minute")
def list_keys(
    request: Request,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth),
):
    return api_keys_service.list_api_keys(db, current_user["id"])


# POST /auth/keys
@router.post(
    "",
    response_model=ApiKeyCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Mint a new API key (plaintext returned once)",
)
@limiter.limit("10/minute")
def create_key(
    request: Request,
    body: ApiKeyCreate,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth),
):
    return api_keys_service.create_api_key(db, current_user["id"], body.label)


# DELETE /auth/keys/{key_id}
@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an API key",
)
@limiter.limit("20/minute")
def delete_key(
    request: Request,
    key_id: int,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth),
):
    deleted = api_keys_service.delete_api_key(db, current_user["id"], key_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
