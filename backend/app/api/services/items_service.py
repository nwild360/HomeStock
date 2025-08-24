from datetime import datetime
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Numeric, String, select, func
from sqlalchemy.orm import declarative_base, Session
from app.api.schemas import ItemCreate, ItemOut, ItemsPage, ItemPatch, StockPatch
from decimal import Decimal

Base = declarative_base()


class Item(Base):
    __tablename__ = "items"
    __table_args__ = {"schema": "homestock"}

    id = Column(BigInteger, primary_key=True)
    name = Column(String)
    type = Column(String)   # domain, but maps as text
    category_id = Column(BigInteger, ForeignKey("homestock.categories.id"))
    mealie_food_id = Column(String)
    notes = Column(String)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))

class ItemStock(Base):
    __tablename__ = "item_stock"
    __table_args__ = {"schema": "homestock"}

    id = Column(BigInteger, ForeignKey("homestock.items.id"), primary_key=True)
    unit_id = Column(BigInteger, ForeignKey("homestock.units.id"))
    quantity = Column(Numeric(10, 2))
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))

# ---- Service Functions ----
# GET /items service: Get paginated list of items with their stock information 
def get_items(session: Session, page: int = 1, page_size: int = 20) -> ItemsPage:
    """
    Retrieve a paginated list of items with their stock information.
    Returns an ItemsPage Pydantic model for API response.
    """
    # Get total count for pagination
    total = session.scalar(select(func.count()).select_from(Item))

    # Join items with item_stock to get quantity and unit_id
    stmt = (
        select(
            Item.id,
            Item.name,
            Item.type,
            Item.category_id,
            Item.mealie_food_id,
            Item.notes,
            ItemStock.quantity,
            ItemStock.unit_id,
            Item.created_at,
            Item.updated_at,
        )
        .select_from(Item)
        .join(ItemStock, ItemStock.id == Item.id, isouter=True)
        .order_by(Item.name.asc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )

    results = session.execute(stmt).all()

    # Convert DB rows to ItemOut Pydantic models
    items = [
        ItemOut(
            id=r.id,
            name=r.name,
            item_type=r.type,  # Map DB 'type' to schema 'item_type'
            category_id=r.category_id,
            mealie_food_id=r.mealie_food_id,
            notes=r.notes,
            quantity=r.quantity if r.quantity is not None else Decimal("0"),
            unit_id=r.unit_id,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in results
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
    Creates a new item and its associated stock record.
    Returns an ItemOut Pydantic model for API response.
    Raises HTTPException on error.
    """
    try:
        # Create the new item
        now = datetime.now().astimezone()
        new_item = Item(
            name=item.name,
            type=item.item_type,  # note: maps from item_type to type
            category_id=item.category_id,
            mealie_food_id=item.mealie_food_id,
            created_at=now,
            updated_at=now,
            notes=""  # Initialize with empty string as per schema
        )
        
        # Add and flush to get the new ID (needed for stock record)
        session.add(new_item)
        session.flush()
        
        # Create the stock record if quantity or unit is provided
        if item.quantity is not None or item.unit_id is not None:
            new_stock = ItemStock(
                id=new_item.id,  # Links to the item we just created
                quantity=item.quantity or Decimal("0"),  # Default to 0 if None
                unit_id=item.unit_id,  # Can be None
                created_at=now,
                updated_at=now
            )
            session.add(new_stock)
        
        # Commit both records
        session.commit()
        
        # Query the created item with its stock info
        created_item = session.execute(
            select(
                Item.id,
                Item.name,
                Item.type.label('item_type'),  # Alias to match schema
                Item.category_id,
                Item.mealie_food_id,
                Item.notes,
                ItemStock.quantity,
                ItemStock.unit_id,
                Item.created_at,
                Item.updated_at
            )
            .outerjoin(ItemStock)
            .where(Item.id == new_item.id)
        ).first()
        
        # Return as ItemOut Pydantic model
        return ItemOut(
            id=created_item.id,
            name=created_item.name,
            item_type=created_item.item_type,
            category_id=created_item.category_id,
            mealie_food_id=created_item.mealie_food_id,
            notes=created_item.notes,
            quantity=created_item.quantity if created_item.quantity is not None else Decimal("0"),
            unit_id=created_item.unit_id,
            created_at=created_item.created_at,
            updated_at=created_item.updated_at,
        )
        
    except IntegrityError as e:
        session.rollback()
        # Handle specific constraint violations
        if 'unique constraint' in str(e.orig).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An item with this name or mealie_food_id already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data provided"
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating item"
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
            Item.id,
            Item.name,
            Item.type.label('item_type'),  # Alias to match schema
            Item.category_id,
            Item.mealie_food_id,
            Item.notes,
            ItemStock.quantity,
            ItemStock.unit_id,
            Item.created_at,
            Item.updated_at
        )
        .outerjoin(ItemStock)
        .where(Item.id == item_id)
    ).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return ItemOut(
        id=result.id,
        name=result.name,
        item_type=result.item_type,
        category_id=result.category_id,
        mealie_food_id=result.mealie_food_id,
        notes=result.notes,
        quantity=result.quantity if result.quantity is not None else Decimal("0"),
        unit_id=result.unit_id,
        created_at=result.created_at,
        updated_at=result.updated_at,
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
        # Fetch the existing item
        item = session.get(Item, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )

        # Concurrency control: If-Unmodified-Since header
        if if_unmodified_since:
            try:
                client_timestamp = datetime.fromisoformat(if_unmodified_since)
                if item.updated_at > client_timestamp:
                    raise HTTPException(
                        status_code=status.HTTP_412_PRECONDITION_FAILED,
                        detail="Item has been modified since the provided timestamp"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid If-Unmodified-Since header format"
                )

        # Track if any field is updated
        updated = False
        # Validate and update fields if provided
        if patch.name is not None:
            if not patch.name.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Name cannot be empty"
                )
            item.name = patch.name
            updated = True
        if patch.category_id is not None:
            item.category_id = patch.category_id
            updated = True
        if patch.notes is not None:
            item.notes = patch.notes
            updated = True

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update"
            )

        # Update the updated_at timestamp
        item.updated_at = datetime.now().astimezone()
        session.add(item)
        session.commit()
        session.refresh(item)

        # Query the updated item with its stock info
        result = session.execute(
            select(
                Item.id,
                Item.name,
                Item.type.label('item_type'),
                Item.category_id,
                Item.mealie_food_id,
                Item.notes,
                ItemStock.quantity,
                ItemStock.unit_id,
                Item.created_at,
                Item.updated_at
            )
            .outerjoin(ItemStock)
            .where(Item.id == item_id)
        ).first()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found after update"
            )
        return ItemOut(
            id=result.id,
            name=result.name,
            item_type=result.item_type,
            category_id=result.category_id,
            mealie_food_id=result.mealie_food_id,
            notes=result.notes,
            quantity=result.quantity if result.quantity is not None else Decimal("0"),
            unit_id=result.unit_id,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating item"
        )

# PATCH /items/{id}/stock service: Update an item's stock information
def patch_stock(session: Session, item_id: int, patch: StockPatch, if_unmodified_since: str | None = None) -> ItemOut:
    """
    Update the stock quantity for an item. Accepts either a delta or a new_qty (mutually exclusive).
    Uses optimistic concurrency control with If-Unmodified-Since header.
    Returns updated ItemOut Pydantic model for API response.
    Raises HTTPException on error.
    """
    try:
        # Fetch the item and its stock record
        item = session.get(Item, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        stock = session.get(ItemStock, item_id)
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stock record not found for item"
            )

        # Concurrency control: If-Unmodified-Since header
        if if_unmodified_since:
            try:
                client_timestamp = datetime.fromisoformat(if_unmodified_since)
                if item.updated_at > client_timestamp:
                    raise HTTPException(
                        status_code=status.HTTP_412_PRECONDITION_FAILED,
                        detail="Item has been modified since the provided timestamp"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid If-Unmodified-Since header format"
                )

        # Input validation: Only one of delta or new_qty must be provided
        if patch.delta is not None and patch.new_qty is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Provide only one of delta or new_qty"
            )
        if patch.delta is None and patch.new_qty is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Must provide either delta or new_qty"
            )

        # Apply the stock update
        if patch.delta is not None:
            new_quantity = (stock.quantity or Decimal("0")) + patch.delta
        else:
            new_quantity = patch.new_qty
        if new_quantity is None or new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Quantity must be non-negative"
            )
        stock.quantity = new_quantity
        stock.updated_at = datetime.now().astimezone()
        item.updated_at = stock.updated_at
        session.add(stock)
        session.add(item)
        session.commit()
        session.refresh(stock)
        session.refresh(item)

        # Query the updated item with its stock info
        result = session.execute(
            select(
                Item.id,
                Item.name,
                Item.type.label('item_type'),
                Item.category_id,
                Item.mealie_food_id,
                Item.notes,
                ItemStock.quantity,
                ItemStock.unit_id,
                Item.created_at,
                Item.updated_at
            )
            .outerjoin(ItemStock)
            .where(Item.id == item_id)
        ).first()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found after stock update"
            )
        return ItemOut(
            id=result.id,
            name=result.name,
            item_type=result.item_type,
            category_id=result.category_id,
            mealie_food_id=result.mealie_food_id,
            notes=result.notes,
            quantity=result.quantity if result.quantity is not None else Decimal("0"),
            unit_id=result.unit_id,
            created_at=result.created_at,
            updated_at=result.updated_at,
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
        # Fetch the item
        item = session.get(Item, item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        # Optionally, check for business rules (e.g., prevent delete if referenced elsewhere)
        # For now, just delete
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