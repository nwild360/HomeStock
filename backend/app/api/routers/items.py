from typing import Optional, Literal, List
from fastapi import APIRouter, Query, Depends, Path, Header, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.api.schemas import ItemsPage, ItemOut, ItemCreate, ItemPatch, StockPatch, BulkItemCreate, BulkItemResult
from app.api.services import items_service
from app.dependencies.db_session import get_dbsession
from app.dependencies.auth import require_auth

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/items", tags=["items"])

# GET /items
@router.get(
    "",
    response_model=ItemsPage,
)
@limiter.limit("100/minute")
def get_items(
    request: Request,
    page: int = Query(1, ge=1, le=10000),
    page_size: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth)
):
    return items_service.get_items(db, page=page, page_size=page_size)

# POST /items
@router.post(
    "",
    response_model=ItemOut,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
async def create_item(
    request: Request,
    body: ItemCreate,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth)
):
    # Create the item
    result = items_service.create_item(db, body)

    return result

# GET /items/{id}
@router.get(
    "/{id}",
    response_model=ItemOut,
)
@limiter.limit("100/minute")
def get_item(
    request: Request,
    id: int,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth)
):
    return items_service.get_item(db, id)

# PATCH /items/{id}
@router.patch(
    "/{id}",
    response_model=ItemOut,
)
@limiter.limit("30/minute")
def update_item(
    request: Request,
    id: int,
    body: ItemPatch,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth),
    if_unmodified_since: str | None = Header(default=None, alias="If-Unmodified-Since"),
):
    return items_service.update_item(db, id, body, if_unmodified_since)

# PATCH /items/{id}/stock
@router.patch(
    "/{id}/stock",
    response_model=ItemOut,
)
@limiter.limit("30/minute")
def patch_stock(
    request: Request,
    id: int,
    body: StockPatch,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth),
    if_unmodified_since: str | None = Header(default=None, alias="If-Unmodified-Since"),
):
    return items_service.patch_stock(db, id, body, if_unmodified_since)

# POST /items/bulk
@router.post(
    "/bulk",
    response_model=List[BulkItemResult],
    status_code=207,
)
@limiter.limit("10/minute")
def bulk_create_items(
    request: Request,
    body: BulkItemCreate,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth),
):
    """Create multiple items in one request. Returns per-item results (207 Multi-Status).
    Results are returned in the same order as the input list."""
    from fastapi import HTTPException as FastAPIHTTPException
    results: List[BulkItemResult] = []
    for item in body.items:
        try:
            created = items_service.create_item(db, item)
            results.append(BulkItemResult(status=201, item=created))
        except FastAPIHTTPException as e:
            db.rollback()
            results.append(BulkItemResult(status=e.status_code, error=str(e.detail)))
        except Exception as e:
            db.rollback()
            results.append(BulkItemResult(status=500, error="Internal error"))
    return results


# DELETE /items/{id}
@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@limiter.limit("20/minute")
def delete_item(
    request: Request,
    id: int,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth)
):
    items_service.delete_item(db, id)