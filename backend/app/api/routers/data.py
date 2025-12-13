from typing import Optional, Literal
from fastapi import APIRouter, Query, Depends, Path, Header, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.api.schemas import CategoryCreate, UnitCreate, CategoryOut, UnitOut, CategoriesPage, UnitsPage
from app.api.services import data_service
from app.dependencies.db_session import get_dbsession
from app.dependencies.auth import require_auth

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/data", tags=["data"])

# GET /categories
@router.get(
    "/categories",
    response_model=CategoriesPage,
)
@limiter.limit("60/minute")
def get_categories(
    request: Request,
    page: int = Query(1, ge=1, le=10000),
    page_size: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth)
):
    return data_service.get_categories(db, page=page, page_size=page_size)

# GET /units
@router.get(
    "/units",
    response_model=UnitsPage,
)
@limiter.limit("60/minute")
def get_units(
    request: Request,
    page: int = Query(1, ge=1, le=10000),
    page_size: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth)
):
    return data_service.get_units(db, page=page, page_size=page_size)

# GET /categories/{id}
@router.get(
    "/categories/{id}",
    response_model=CategoryOut,
)
@limiter.limit("60/minute")
def get_category(
    request: Request,
    id: int,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth)
):
    return data_service.get_category(db, id)

# GET /units/{id}
@router.get(
    "/units/{id}",
    response_model=UnitOut,
)
@limiter.limit("60/minute")
def get_unit(
    request: Request,
    id: int,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth)
):
    return data_service.get_unit(db, id)

# POST /categories
@router.post(
    "/categories",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
async def create_category(
    request: Request,
    body: CategoryCreate,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth)
):
    result = data_service.create_category(db, body)

    return result

# POST /units
@router.post(
    "/units",
    response_model=UnitOut,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
async def create_unit(
    request: Request,
    body: UnitCreate,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth)
):
    result = data_service.create_unit(db, body)

    return result

# PATCH /categories/{id}
@router.patch(
    "/categories/{id}",
    response_model=CategoryOut,
)
@limiter.limit("20/minute")
def update_category(
    request: Request,
    id: int,
    body: CategoryCreate,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth),
    if_unmodified_since: str | None = Header(default=None, alias="If-Unmodified-Since"),
):
    return data_service.update_category(db, id, body, if_unmodified_since)

# PATCH /units/{id}
@router.patch(
    "/units/{id}",
    response_model=UnitOut,
)
@limiter.limit("20/minute")
def update_unit(
    request: Request,
    id: int,
    body: UnitCreate,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth),
    if_unmodified_since: str | None = Header(default=None, alias="If-Unmodified-Since"),
):
    return data_service.update_unit(db, id, body, if_unmodified_since)

# DELETE /categories
@router.delete(
    "/categories/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@limiter.limit("10/minute")
def delete_category(
    request: Request,
    id: int,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth)
):
    data_service.delete_category(db, id)

# DELETE /units
@router.delete(
    "/units/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@limiter.limit("10/minute")
def delete_unit(
    request: Request,
    id: int,
    db: Session = Depends(get_dbsession),
    current_user: dict = Depends(require_auth)
):
    data_service.delete_unit(db, id)