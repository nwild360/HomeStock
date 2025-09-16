from typing import Optional, Literal
from fastapi import APIRouter, Query, Depends, Path, Header, status, Request
from sqlalchemy.orm import Session
from app.api.schemas import *
from app.api.services import items_service
from app.dependencies.db_session import get_dbsession
from app.dependencies.auth import require_auth_api_key

router = APIRouter(prefix="/items", tags=["items"])

# GET /items
@router.get(
    "",
    response_model=ItemsPage,
    dependencies=[Depends(require_auth_api_key)],
)
def get_items(
    page: int = Query(1, ge=1, le=10000),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_dbsession)
):
    return items_service.get_items(db, page=page, page_size=page_size)

# POST /items
@router.post(
    "", 
    response_model=ItemOut, 
    status_code=status.HTTP_201_CREATED, 
    dependencies=[Depends(require_auth_api_key)]
)
async def create_item(
    request: Request,
    body: ItemCreate,
    db: Session = Depends(get_dbsession),
):
    # Create the item
    result = items_service.create_item(db, body)
    
    return result

# GET /items/{id}
@router.get(
    "/{id}", 
    response_model=ItemOut,
    dependencies=[Depends(require_auth_api_key)],
)
def get_item(id: int, db=Depends(get_dbsession)):
    return items_service.get_item(db, id)

# PATCH /items/{id}
@router.patch(
    "/{id}",
    response_model=ItemOut,
    dependencies=[Depends(require_auth_api_key)],
)
def update_item(
    id: int,
    body: ItemPatch,
    db=Depends(get_dbsession),
    if_unmodified_since: str | None = Header(default=None, alias="If-Unmodified-Since"),
):
    return items_service.update_item(db, id, body, if_unmodified_since)

# PATCH /items/{id}/stock
@router.patch(
    "/{id}/stock",
    response_model=ItemOut,
    dependencies=[Depends(require_auth_api_key)], 
)
def patch_stock(
    id: int,
    body: StockPatch,
    db=Depends(get_dbsession),
    if_unmodified_since: str | None = Header(default=None, alias="If-Unmodified-Since"),
):
    return items_service.patch_stock(db, id, body, if_unmodified_since)

# DELETE /items/{id}
@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_auth_api_key)],
)
def delete_item(
    id: int,
    db=Depends(get_dbsession)
): 
    items_service.delete_item(db, id)