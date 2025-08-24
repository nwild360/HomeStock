# app/api/schemas.py
from typing import Optional, Literal, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field

# ---- Items ----
class ItemOut(BaseModel):
    id: int
    name: str
    item_type: Literal["food", "household","equipment"]
    category_id: int
    mealie_food_id: Optional[str] = None
    quantity: Decimal = Decimal("0")
    unit_id: Optional[int] = None
    notes: str
    created_at: datetime
    updated_at: datetime

class ItemsPage(BaseModel):
    items: List[ItemOut]
    page: int = 1
    page_size: int = 20
    total: int = 0

class ItemCreate(BaseModel):
    name: str
    item_type: Literal["food", "household","equipment"]
    category_id: Optional[int] = None
    quantity: Optional[Decimal] = None
    unit_id: Optional[int] = None
    mealie_food_id: Optional[str] = None

class ItemPatch(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    notes: Optional[str] = None

class StockPatch(BaseModel):
    delta: Optional[Decimal] = Field(default=None, description="Mutually exclusive with new_qty")
    new_qty: Optional[Decimal] = Field(default=None, description="Mutually exclusive with delta")

# ---- Lookups ----
class CategoryOut(BaseModel):
    id: int
    name: str

class UnitOut(BaseModel):
    id: int
    name: str
    abbreviation: Optional[str] = None

# ---- Foods search ----
class FoodHit(BaseModel):
    source: Literal["local", "mealie"]
    id: str
    name: str
    on_hand: Optional[bool] = None
