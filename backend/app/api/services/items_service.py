from datetime import datetime
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Numeric, String, select, func, text
from sqlalchemy.orm import declarative_base, Session
from app.api.schemas import ItemCreate, ItemOut, ItemsPage, ItemPatch, StockPatch
from decimal import Decimal

Base = declarative_base()

class Items(Base):
    __tablename__ = "items"
    __table_args__ = {"schema": "homestock"}

    id = Column(BigInteger, primary_key=True)
    name = Column(String)
    type = Column(String)   # domain, but maps as text
    category_id = Column(BigInteger, ForeignKey("homestock.categories.id"))
    quantity = Column(Numeric(10, 2))
    unit_id = Column(BigInteger, ForeignKey("homestock.units.id"))
    mealie_food_id = Column(String)
    notes = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class Categories(Base):
    __tablename__ = "categories"
    __table_args__ = {"schema": "homestock"}
    id = Column(BigInteger, primary_key=True)
    name = Column(String)

class Units(Base):
    __tablename__ = "units"
    __table_args__ = {"schema": "homestock"}
    id = Column(BigInteger, primary_key=True)
    name = Column(String)
    abbreviation = Column(String)

# ---- Service Functions ----
# GET /items service: Get paginated list of items with their stock information 
def get_items(session: Session, page: int = 1, page_size: int = 20) -> ItemsPage:
    """
    Retrieve a paginated list of items with their stock information.
    Returns an ItemsPage Pydantic model for API response.
    """
    # Get total count for pagination
    total = session.scalar(select(func.count()).select_from(Items))

    stmt = (
        select(
            Items.id.label("item_id"),
            Items.name.label("item_name"),
            Items.type.label("item_type"),
            Categories.name.label("category_name"),
            Items.mealie_food_id.label("mealie_food_id"),
            Items.notes.label("notes"),
            Items.quantity.label("quantity"),
            Units.name.label("unit_name"),
            Items.created_at.label("created_at"),
            Items.updated_at.label("updated_at"),
        )
        .join(Categories, Categories.id == Items.category_id, isouter=True)
        .join(Units, Units.id == Items.unit_id, isouter=True)
        .order_by(Items.name.asc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )

    results = session.execute(stmt).all()

    items = [
        ItemOut(
            item_id=row.item_id,
            item_name=row.item_name,
            item_type=row.item_type,
            category_name=row.category_name,
            mealie_food_id=row.mealie_food_id,
            notes=row.notes,
            quantity=row.quantity if row.quantity is not None else Decimal("0"),
            unit_name=row.unit_name,
            created_at=row.created_at,
            updated_at=row.updated_at
        )
        for row in results
    ]

    # Return as ItemsPage Pydantic model
    return ItemsPage(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )

# POST /items service: Create a new item with optional initial stock
def create_item(session: Session, item: ItemCreate) -> ItemOut:
    """
    Creates a new item with its stock record.
    Returns an ItemOut Pydantic model for API response.
    Raises HTTPException on error.
    """
    try:
        # Validate category if provided
        category_id = None
        if item.category_name is not None:
            category = session.execute(
                select(Categories).where(Categories.name == item.category_name)
            ).scalar_one_or_none()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category not found"
                )
            category_id = category.id
        # Validate unit if provided
        unit_id = None
        if item.unit_name is not None:
            unit = session.execute(
                select(Units).where(Units.name == item.unit_name)
            ).scalar_one_or_none()
            if not unit:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unit not found"
                )
            unit_id = unit.id
        new_item = Items(
            name=item.item_name,
            type=item.item_type,
            category_id=category_id,
            quantity=item.quantity,
            unit_id=unit_id,
            notes=item.notes,
            mealie_food_id=item.mealie_food_id,
        )
        session.add(new_item)
        session.commit()
        session.refresh(new_item)
        # Get category/unit names for output
        category_name = None
        if new_item.category_id:
            category = session.get(Categories, new_item.category_id)
            category_name = category.name if category else None
        unit_name = None
        if new_item.unit_id:
            unit = session.get(Units, new_item.unit_id)
            unit_name = unit.name if unit else None
        return ItemOut(
            item_id=new_item.id,
            item_name=new_item.name,
            item_type=new_item.type,
            category_name=category_name,
            mealie_food_id=new_item.mealie_food_id,
            notes=new_item.notes,
            quantity=new_item.quantity,
            unit_name=unit_name,
            created_at=new_item.created_at,
            updated_at=new_item.updated_at
        )
    except IntegrityError as e:
        session.rollback()
        if 'unique constraint' in str(e.orig).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An item with this name already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data provided"
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# GET /items/{id} service: Get a single item by ID with its stock information
def get_item(session: Session, item_id: int) -> ItemOut:
    """
    Retrieve a single item by ID with its stock information.
    Returns an ItemOut Pydantic model for API response.
    Raises HTTPException if not found.
    """
    result = session.execute(
        select(
            Items.id.label("item_id"),
            Items.name.label("item_name"),
            Items.type.label("item_type"),
            Categories.name.label("category_name"),
            Items.mealie_food_id.label("mealie_food_id"),
            Items.notes.label("notes"),
            Items.quantity.label("quantity"),
            Units.name.label("unit_name"),
            Items.created_at.label("created_at"),
            Items.updated_at.label("updated_at")
        )
        .join(Categories, Categories.id == Items.category_id, isouter=True)
        .join(Units, Units.id == Items.unit_id, isouter=True)
        .where(Items.id == item_id)
    ).first()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return ItemOut(
        item_id=result.item_id,
        item_name=result.item_name,
        item_type=result.item_type,
        category_name=result.category_name,
        mealie_food_id=result.mealie_food_id,
        notes=result.notes,
        quantity=result.quantity if result.quantity is not None else Decimal("0"),
        unit_name=result.unit_name,
        created_at=result.created_at,
        updated_at=result.updated_at
    )

# PATCH /items/{id} service: Update an item's mutable fields
def update_item(session: Session, item_id: int, patch: ItemPatch, if_unmodified_since: str | None = None) -> ItemOut:
    """
    Update an item's mutable fields: name, category_id, notes.
    Uses optimistic concurrency control with If-Unmodified-Since header.
    Returns updated ItemOut Pydantic model for API response.
    Raises HTTPException on error.
    """
    try:
        item = session.get(Items, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        if if_unmodified_since:
            try:
                client_timestamp = datetime.fromisoformat(if_unmodified_since)
                if item.updated_at and item.updated_at > client_timestamp:
                    raise HTTPException(
                        status_code=status.HTTP_412_PRECONDITION_FAILED,
                        detail="Item has been modified since the provided timestamp"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid If-Unmodified-Since header format"
                )
        updated = False
        if patch.name is not None:
            if not patch.name.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Name cannot be empty"
                )
            item.name = patch.name
            updated = True
        if patch.category_name is not None:
            category = session.execute(
                select(Categories).where(Categories.name == patch.category_name)
            ).scalar_one_or_none()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category not found"
                )
            item.category_id = category.id
            updated = True
        if patch.notes is not None:
            item.notes = patch.notes
            updated = True
        if patch.quantity is not None:
            if patch.quantity < 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Quantity cannot be negative"
                )
            item.quantity = patch.quantity
            updated = True
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update"
            )
        session.add(item)
        session.commit()
        session.refresh(item)
        # Get category/unit names for output
        category_name = None
        if item.category_id:
            category = session.get(Categories, item.category_id)
            category_name = category.name if category else None
        unit_name = None
        if item.unit_id:
            unit = session.get(Units, item.unit_id)
            unit_name = unit.name if unit else None
        return ItemOut(
            item_id=item.id,
            item_name=item.name,
            item_type=item.type,
            category_name=category_name,
            mealie_food_id=item.mealie_food_id,
            notes=item.notes,
            quantity=item.quantity if item.quantity is not None else Decimal("0"),
            unit_name=unit_name,
            created_at=item.created_at,
            updated_at=item.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating item"
        )

# PATCH /items/{id}/stock service: Update item stock quantity
def patch_stock(session: Session, item_id: int, stock_patch: StockPatch, if_unmodified_since: str | None = None) -> ItemOut:
    """
    Update an item's stock quantity using either delta or new_qty.
    Uses optimistic concurrency control with If-Unmodified-Since header.
    Returns updated ItemOut Pydantic model for API response.
    Raises HTTPException on error.
    """
    try:
        item = session.get(Items, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )

        # Validate mutually exclusive fields
        if stock_patch.delta is not None and stock_patch.new_qty is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot specify both delta and new_qty"
            )

        if stock_patch.delta is None and stock_patch.new_qty is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Must specify either delta or new_qty"
            )

        # Optimistic locking check
        if if_unmodified_since:
            try:
                client_timestamp = datetime.fromisoformat(if_unmodified_since)
                if item.updated_at and item.updated_at > client_timestamp:
                    raise HTTPException(
                        status_code=status.HTTP_412_PRECONDITION_FAILED,
                        detail="Item has been modified since the provided timestamp"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid If-Unmodified-Since header format"
                )

        # Calculate new quantity
        current_qty = item.quantity if item.quantity is not None else Decimal("0")

        if stock_patch.delta is not None:
            new_quantity = current_qty + stock_patch.delta
        else:  # new_qty is not None
            new_quantity = stock_patch.new_qty

        # Validate new quantity is non-negative
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Quantity cannot be negative"
            )

        # Update quantity (updated_at will be set automatically by DB trigger)
        item.quantity = new_quantity

        session.add(item)
        session.commit()
        session.refresh(item)

        # Get category/unit names for output
        category_name = None
        if item.category_id:
            category = session.get(Categories, item.category_id)
            category_name = category.name if category else None

        unit_name = None
        if item.unit_id:
            unit = session.get(Units, item.unit_id)
            unit_name = unit.name if unit else None

        return ItemOut(
            item_id=item.id,
            item_name=item.name,
            item_type=item.type,
            category_name=category_name,
            mealie_food_id=item.mealie_food_id,
            notes=item.notes,
            quantity=item.quantity if item.quantity is not None else Decimal("0"),
            unit_name=unit_name,
            created_at=item.created_at,
            updated_at=item.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating stock"
        )


# DELETE /items/{id} service: Delete an item by ID
def delete_item(session: Session, item_id: int) -> None:
    """
    Safely delete an item and its stock record by item_id.
    Raises HTTPException if not found or on error.
    """
    try:
        item = session.get(Items, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        session.delete(item)
        session.commit()
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting item"
        )