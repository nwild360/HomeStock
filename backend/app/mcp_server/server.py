"""
FastMCP server exposing HomeStock inventory operations as MCP tools.

Tools call the existing service layer directly (same code paths as the REST
API). Auth and the feature toggle are enforced upstream by McpAuthMiddleware;
every handler runs with the authenticated user available via get_current_user().

Tools are plain sync functions — FastMCP runs them in a thread pool, matching
the app's synchronous SQLAlchemy services.
"""
import logging
from contextlib import contextmanager
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal, Optional

from fastapi import HTTPException
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings

from app.api.schemas import CategoryCreate, ItemCreate, ItemPatch, StockPatch, UnitCreate
from app.api.services import data_service, items_service
from app.dependencies.db_session import DBSession
from app.mcp_server.context import get_current_user

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "HomeStock",
    instructions=(
        "Manage the HomeStock home inventory: food and household items with quantities, "
        "plus the categories and measurement units they reference. Items reference "
        "categories and units by name; create them first if they don't exist yet."
    ),
    stateless_http=True,   # each request is independent; safe across container restarts
    json_response=True,    # plain JSON responses instead of SSE; tools are short sync calls
    streamable_http_path="/",  # served via an exact Route at /mcp (see main.py)
    # FastMCP defaults to localhost-only Host validation (DNS-rebinding protection),
    # which would 421 requests arriving via nginx on the real domain. Rebinding
    # attacks target unauthenticated localhost servers; every request here must
    # carry an OAuth token or API key, so Host pinning adds nothing.
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


@contextmanager
def db_session():
    """One DB session per tool call (FastAPI dependency injection doesn't apply here)."""
    db = DBSession()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def service_errors():
    """Convert service-layer HTTPExceptions into readable, actionable tool errors."""
    try:
        yield
    except HTTPException as e:
        raise ToolError(f"{e.status_code}: {e.detail}") from e


def _audit(tool: str) -> dict:
    user = get_current_user()
    logger.info("MCP tool %s called by %s", tool, user["username"])
    return user


def _decimal(value: float | None, field: str) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation as e:
        raise ToolError(f"422: {field} is not a valid number") from e


def _date(value: str | None, field: str) -> Optional[date]:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as e:
        raise ToolError(f"422: {field} must be an ISO date (YYYY-MM-DD)") from e


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

@mcp.tool()
def list_items(page: int = 1, page_size: int = 20) -> dict:
    """List inventory items with quantities, paginated alphabetically by name.

    Args:
        page: Page number, starting at 1.
        page_size: Items per page (default 20).
    """
    _audit("list_items")
    with db_session() as db, service_errors():
        return items_service.get_items(db, page, page_size).model_dump(mode="json")


@mcp.tool()
def get_item(item_id: int) -> dict:
    """Get a single inventory item by its ID.

    Args:
        item_id: The item's numeric ID.
    """
    _audit("get_item")
    with db_session() as db, service_errors():
        return items_service.get_item(db, item_id).model_dump(mode="json")


@mcp.tool()
def create_item(
    name: str,
    item_type: Literal["food", "household"],
    quantity: float,
    category_name: Optional[str] = None,
    unit_name: Optional[str] = None,
    notes: Optional[str] = None,
    expiration_date: Optional[str] = None,
    date_bought: Optional[str] = None,
) -> dict:
    """Create a new inventory item. Category and unit are referenced by name and must already exist (see list_categories / list_units).

    Args:
        name: Item name, e.g. "Whole Milk".
        item_type: Either "food" or "household".
        quantity: Initial stock quantity (>= 0).
        category_name: Existing category name, or omit for none.
        unit_name: Existing unit name, or omit for none.
        notes: Free-text notes (max 1000 chars).
        expiration_date: ISO date (YYYY-MM-DD).
        date_bought: ISO date (YYYY-MM-DD).
    """
    _audit("create_item")
    body = ItemCreate(
        item_name=name,
        item_type=item_type,
        quantity=_decimal(quantity, "quantity"),
        category_name=category_name,
        unit_name=unit_name,
        notes=notes or "",
        expiration_date=_date(expiration_date, "expiration_date"),
        date_bought=_date(date_bought, "date_bought"),
    )
    with db_session() as db, service_errors():
        return items_service.create_item(db, body).model_dump(mode="json")


@mcp.tool()
def update_item(
    item_id: int,
    name: Optional[str] = None,
    category_name: Optional[str] = None,
    unit_name: Optional[str] = None,
    quantity: Optional[float] = None,
    notes: Optional[str] = None,
    expiration_date: Optional[str] = None,
    date_bought: Optional[str] = None,
) -> dict:
    """Update fields of an existing item; only the provided fields change.

    Args:
        item_id: The item's numeric ID.
        name: New item name.
        category_name: Existing category name to assign.
        unit_name: Existing unit name to assign.
        quantity: New absolute quantity (>= 0). Prefer adjust_stock for +/- changes.
        notes: New notes text.
        expiration_date: ISO date (YYYY-MM-DD).
        date_bought: ISO date (YYYY-MM-DD).
    """
    _audit("update_item")
    patch = ItemPatch(
        name=name,
        category_name=category_name,
        unit_name=unit_name,
        quantity=_decimal(quantity, "quantity"),
        notes=notes,
        expiration_date=_date(expiration_date, "expiration_date"),
        date_bought=_date(date_bought, "date_bought"),
    )
    with db_session() as db, service_errors():
        return items_service.update_item(db, item_id, patch, None).model_dump(mode="json")


@mcp.tool()
def adjust_stock(item_id: int, delta: Optional[float] = None, new_qty: Optional[float] = None) -> dict:
    """Adjust an item's stock: pass delta (positive or negative change) OR new_qty (absolute value), not both.

    Args:
        item_id: The item's numeric ID.
        delta: Change to apply, e.g. -1 after using one, +6 after buying six.
        new_qty: Absolute quantity to set (>= 0).
    """
    _audit("adjust_stock")
    body = StockPatch(delta=_decimal(delta, "delta"), new_qty=_decimal(new_qty, "new_qty"))
    with db_session() as db, service_errors():
        return items_service.patch_stock(db, item_id, body, None).model_dump(mode="json")


@mcp.tool()
def delete_item(item_id: int) -> dict:
    """Permanently delete an inventory item.

    Args:
        item_id: The item's numeric ID.
    """
    _audit("delete_item")
    with db_session() as db, service_errors():
        items_service.delete_item(db, item_id)
    return {"deleted": True, "item_id": item_id}


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

@mcp.tool()
def list_categories(page: int = 1, page_size: int = 100) -> dict:
    """List item categories, paginated alphabetically by name.

    Args:
        page: Page number, starting at 1.
        page_size: Categories per page (default 100).
    """
    _audit("list_categories")
    with db_session() as db, service_errors():
        return data_service.get_categories(db, page, page_size).model_dump(mode="json")


@mcp.tool()
def create_category(name: str, description: Optional[str] = None) -> dict:
    """Create a new item category.

    Args:
        name: Category name, e.g. "Dairy" (must be unique).
        description: Optional description (max 1000 chars).
    """
    _audit("create_category")
    body = CategoryCreate(name=name, description=description)
    with db_session() as db, service_errors():
        return data_service.create_category(db, body).model_dump(mode="json")


@mcp.tool()
def update_category(category_id: int, name: str, description: Optional[str] = None) -> dict:
    """Update a category's name and description (full replace of both fields).

    Args:
        category_id: The category's numeric ID.
        name: New category name.
        description: New description, or omit to clear it.
    """
    _audit("update_category")
    body = CategoryCreate(name=name, description=description)
    with db_session() as db, service_errors():
        return data_service.update_category(db, category_id, body, None).model_dump(mode="json")


@mcp.tool()
def delete_category(category_id: int) -> dict:
    """Delete a category. Items keep existing but lose the category (set to none).

    Args:
        category_id: The category's numeric ID.
    """
    _audit("delete_category")
    with db_session() as db, service_errors():
        data_service.delete_category(db, category_id)
    return {"deleted": True, "category_id": category_id}


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------

@mcp.tool()
def list_units(page: int = 1, page_size: int = 100) -> dict:
    """List measurement units, paginated alphabetically by name.

    Args:
        page: Page number, starting at 1.
        page_size: Units per page (default 100).
    """
    _audit("list_units")
    with db_session() as db, service_errors():
        return data_service.get_units(db, page, page_size).model_dump(mode="json")


@mcp.tool()
def create_unit(name: str, abbreviation: Optional[str] = None) -> dict:
    """Create a measurement unit.

    Args:
        name: Unit name, e.g. "ounce" (must be unique).
        abbreviation: Short form, e.g. "oz" (must be unique).
    """
    _audit("create_unit")
    body = UnitCreate(name=name, abbreviation=abbreviation)
    with db_session() as db, service_errors():
        return data_service.create_unit(db, body).model_dump(mode="json")


@mcp.tool()
def update_unit(unit_id: int, name: str, abbreviation: Optional[str] = None) -> dict:
    """Update a unit's name and abbreviation (full replace of both fields).

    Args:
        unit_id: The unit's numeric ID.
        name: New unit name.
        abbreviation: New abbreviation, or omit to clear it.
    """
    _audit("update_unit")
    body = UnitCreate(name=name, abbreviation=abbreviation)
    with db_session() as db, service_errors():
        return data_service.update_unit(db, unit_id, body, None).model_dump(mode="json")


@mcp.tool()
def delete_unit(unit_id: int) -> dict:
    """Delete a unit. Items keep existing but lose the unit (set to none).

    Args:
        unit_id: The unit's numeric ID.
    """
    _audit("delete_unit")
    with db_session() as db, service_errors():
        data_service.delete_unit(db, unit_id)
    return {"deleted": True, "unit_id": unit_id}
