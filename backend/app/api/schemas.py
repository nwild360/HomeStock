# app/api/schemas.py
from typing import Optional, Literal, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field

# ---- Items ----
class ItemOut(BaseModel):
    item_id: int
    item_name: str
    item_type: Literal["food", "household"]
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
    #created_at: datetime

class ItemPatch(BaseModel):
    name: Optional[str] = None
    category_name: Optional[str] = None
    unit_name: Optional[str] = None
    quantity: Optional[Decimal] = Field(default=None, ge=0)
    notes: Optional[str] = None
    #updated_at: datetime

class StockPatch(BaseModel):
    delta: Optional[Decimal] = Field(default=None, description="Mutually exclusive with new_qty")
    new_qty: Optional[Decimal] = Field(default=None, description="Mutually exclusive with delta")

# ---- Data Tags ----
class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None

class UnitCreate(BaseModel):
    name: str
    abbreviation: Optional[str] = None    

class CategoryOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

class UnitOut(BaseModel):
    id: int
    name: str
    abbreviation: Optional[str] = None

class CategoriesPage(BaseModel):
    items: List[CategoryOut]
    page: int = 1
    page_size: int = 10
    total: int = 0

class UnitsPage(BaseModel):
    items: List[UnitOut]
    page: int = 1
    page_size: int = 10
    total: int = 0

# ---- Foods search ----
class FoodHit(BaseModel):
    source: Literal["local", "mealie"]
    id: str
    name: str
    on_hand: Optional[bool] = None

# ---- Authentication ----
class Token(BaseModel):
    """Response model for successful login."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Data extracted from JWT token."""
    username: Optional[str] = None

class UserCreate(BaseModel):
    """Request model for user registration."""
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    password: str = Field(..., min_length=8, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')

class UserOut(BaseModel):
    """Response model for user data (no password)."""
    id: int
    username: str

class UserLogin(BaseModel):
    """Request model for user login (used with form data)."""
    username: str
    password: str

class PasswordChange(BaseModel):
    """Request model for changing user password."""
    current_password: str = Field(..., min_length=1, description="Current password for verification")
    new_password: str = Field(..., min_length=8, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$', description="New password (8-100 chars, alphanumeric with _-)")

class UsernameChange(BaseModel):
    """Request model for changing username."""
    new_username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$', description="New username (3-50 chars, alphanumeric with _-)")
