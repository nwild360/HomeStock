# app/api/schemas.py
from typing import Optional, Literal, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field

# ---- Items ----
class ItemOut(BaseModel):
    item_id: int
    item_name: str
    item_type: Literal["food", "household","equipment"]
    category_name: Optional[str]
    mealie_food_id: Optional[str] = None
    quantity: Decimal = Field(..., ge=0)
    unit_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ItemsPage(BaseModel):
    items: List[ItemOut]
    page: int = 1
    page_size: int = 10
    total: int = 0

class ItemCreate(BaseModel):
    item_name: str = Field(..., min_length=1, max_length=255)
    item_type: Literal["food", "household"]
    category_name: Optional[str] = Field(default=None, example="Pantry")
    quantity: Decimal = Field(..., ge=0)  # Make quantity required
    unit_name: Optional[str] = Field(default=None, example=None)
    notes: Optional[str] = Field(default="", max_length=1000)  # Make notes optional with empty string default
    mealie_food_id: Optional[str] = None  # Add mealie_food_id as optional
    created_at: datetime

class ItemPatch(BaseModel):
    name: Optional[str] = None
    category_name: Optional[int] = None
    quantity: Optional[Decimal] = Field(default=None, ge=0)
    notes: Optional[str] = None
    updated_at: datetime

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
