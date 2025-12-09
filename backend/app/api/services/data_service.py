from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.api.schemas import CategoryCreate, UnitCreate, CategoryOut, UnitOut, CategoriesPage, UnitsPage
from app.api.services.items_service import Categories, Units

# ---- Categories Service Functions ----

def get_categories(session: Session, page: int = 1, page_size: int = 20) -> CategoriesPage:
    """
    Retrieve a paginated list of categories.
    Returns a CategoriesPage Pydantic model for API response.
    """
    # Get total count for pagination
    total = session.scalar(select(func.count()).select_from(Categories))

    stmt = (
        select(Categories)
        .order_by(Categories.name.asc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )

    results = session.execute(stmt).scalars().all()

    items = [
        CategoryOut(
            id=category.id,
            name=category.name,
            description=category.description
        )
        for category in results
    ]

    return CategoriesPage(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


def get_category(session: Session, category_id: int) -> CategoryOut:
    """
    Retrieve a single category by ID.
    Returns a CategoryOut Pydantic model for API response.
    Raises HTTPException if not found.
    """
    category = session.get(Categories, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    return CategoryOut(
        id=category.id,
        name=category.name,
        description=category.description
    )


def create_category(session: Session, category: CategoryCreate) -> CategoryOut:
    """
    Creates a new category.
    Returns a CategoryOut Pydantic model for API response.
    Raises HTTPException on error.
    """
    try:
        new_category = Categories(
            name=category.name,
            description=category.description
        )
        session.add(new_category)
        session.commit()
        session.refresh(new_category)

        return CategoryOut(
            id=new_category.id,
            name=new_category.name,
            description=new_category.description
        )
    except IntegrityError as e:
        session.rollback()
        if 'unique constraint' in str(e.orig).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A category with this name already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data provided"
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the category"
        )


def update_category(session: Session, category_id: int, category: CategoryCreate, if_unmodified_since: str | None = None) -> CategoryOut:
    """
    Update a category's fields.
    Returns updated CategoryOut Pydantic model for API response.
    Raises HTTPException on error.
    """
    try:
        existing_category = session.get(Categories, category_id)
        if not existing_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        # Update fields
        existing_category.name = category.name
        existing_category.description = category.description

        session.add(existing_category)
        session.commit()
        session.refresh(existing_category)

        return CategoryOut(
            id=existing_category.id,
            name=existing_category.name,
            description=existing_category.description
        )
    except IntegrityError as e:
        session.rollback()
        if 'unique constraint' in str(e.orig).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A category with this name already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data provided"
        )
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating category"
        )


def delete_category(session: Session, category_id: int) -> None:
    """
    Delete a category by ID.
    Raises HTTPException if not found or on error.
    """
    try:
        category = session.get(Categories, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        session.delete(category)
        session.commit()
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting category"
        )


# ---- Units Service Functions ----

def get_units(session: Session, page: int = 1, page_size: int = 20) -> UnitsPage:
    """
    Retrieve a paginated list of units.
    Returns a UnitsPage Pydantic model for API response.
    """
    # Get total count for pagination
    total = session.scalar(select(func.count()).select_from(Units))

    stmt = (
        select(Units)
        .order_by(Units.name.asc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )

    results = session.execute(stmt).scalars().all()

    items = [
        UnitOut(
            id=unit.id,
            name=unit.name,
            abbreviation=unit.abbreviation
        )
        for unit in results
    ]

    return UnitsPage(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


def get_unit(session: Session, unit_id: int) -> UnitOut:
    """
    Retrieve a single unit by ID.
    Returns a UnitOut Pydantic model for API response.
    Raises HTTPException if not found.
    """
    unit = session.get(Units, unit_id)
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found"
        )

    return UnitOut(
        id=unit.id,
        name=unit.name,
        abbreviation=unit.abbreviation
    )


def create_unit(session: Session, unit: UnitCreate) -> UnitOut:
    """
    Creates a new unit.
    Returns a UnitOut Pydantic model for API response.
    Raises HTTPException on error.
    """
    try:
        new_unit = Units(
            name=unit.name,
            abbreviation=unit.abbreviation
        )
        session.add(new_unit)
        session.commit()
        session.refresh(new_unit)

        return UnitOut(
            id=new_unit.id,
            name=new_unit.name,
            abbreviation=new_unit.abbreviation
        )
    except IntegrityError as e:
        session.rollback()
        if 'unique constraint' in str(e.orig).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A unit with this name or abbreviation already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data provided"
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the unit"
        )


def update_unit(session: Session, unit_id: int, unit: UnitCreate, if_unmodified_since: str | None = None) -> UnitOut:
    """
    Update a unit's fields.
    Returns updated UnitOut Pydantic model for API response.
    Raises HTTPException on error.
    """
    try:
        existing_unit = session.get(Units, unit_id)
        if not existing_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )

        # Update fields
        existing_unit.name = unit.name
        existing_unit.abbreviation = unit.abbreviation

        session.add(existing_unit)
        session.commit()
        session.refresh(existing_unit)

        return UnitOut(
            id=existing_unit.id,
            name=existing_unit.name,
            abbreviation=existing_unit.abbreviation
        )
    except IntegrityError as e:
        session.rollback()
        if 'unique constraint' in str(e.orig).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A unit with this name or abbreviation already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data provided"
        )
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating unit"
        )


def delete_unit(session: Session, unit_id: int) -> None:
    """
    Delete a unit by ID.
    Raises HTTPException if not found or on error.
    """
    try:
        unit = session.get(Units, unit_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )
        session.delete(unit)
        session.commit()
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting unit"
        )
