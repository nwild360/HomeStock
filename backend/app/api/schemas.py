# app/api/schemas.py
from typing import Optional, Literal, List
from decimal import Decimal
from datetime import datetime, date
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
    expiration_date: Optional[date] = None
    date_bought: Optional[date] = None
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
    quantity: Decimal = Field(..., ge=0)
    unit_name: Optional[str] = Field(default=None, example=None)
    notes: Optional[str] = Field(default="", max_length=1000)
    mealie_food_id: Optional[str] = None
    expiration_date: Optional[date] = None
    date_bought: Optional[date] = None

class ItemPatch(BaseModel):
    name: Optional[str] = None
    category_name: Optional[str] = None
    unit_name: Optional[str] = None
    quantity: Optional[Decimal] = Field(default=None, ge=0)
    notes: Optional[str] = None
    expiration_date: Optional[date] = None
    date_bought: Optional[date] = None

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
    password: str = Field(..., min_length=8, max_length=100, pattern=r'^[a-zA-Z0-9_\-!@#$%^&*()=+]+$')  # Allow safe special chars for stronger passwords

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
    new_password: str = Field(..., min_length=8, max_length=100, pattern=r'^[a-zA-Z0-9_\-!@#$%^&*()=+]+$', description="New password (8-100 chars, allow safe special chars)")

class UsernameChange(BaseModel):
    """Request model for changing username."""
    new_username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$', description="New username (3-50 chars, alphanumeric with _-)")

# ---- API Keys ----
class ApiKeyCreate(BaseModel):
    """Request model for minting a new API key."""
    label: str = Field(..., min_length=1, max_length=100, description="Human-readable name for the key")

class ApiKeyOut(BaseModel):
    """Response model for an API key (never includes the secret)."""
    id: int
    label: str
    key_prefix: str
    created_at: datetime
    last_used_at: Optional[datetime] = None

class ApiKeyCreated(ApiKeyOut):
    """Response model returned once at creation, including the one-time plaintext key."""
    key: str

# ---- OIDC ----
class OidcConfig(BaseModel):
    """Public OIDC config returned to unauthenticated clients (no secret)."""
    enabled: bool
    client_id: Optional[str] = None

class OidcSettings(BaseModel):
    """Full OIDC settings for admin read/write."""
    enabled: bool
    issuer_url: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None

# ---- Backups ----
class BackupItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, pattern=r"^homestock_\d{4}-\d{2}-\d{2}_\d{6}\.zip$")
    created_at: datetime
    size_bytes: int = Field(..., ge=0)

class BackupList(BaseModel):
    backups: List[BackupItem]
    total: int

# ---- MCP Server ----
class McpConfig(BaseModel):
    """Public MCP server config (no details exposed)."""
    enabled: bool

class McpSettings(BaseModel):
    """Full MCP server settings for admin read/write."""
    enabled: bool
    allow_api_keys: bool = False
    server_url: Optional[str] = None
    required_scope: Optional[str] = "mcp:tools"

# ---- Receipt Scan ----
class ReceiptScanConfig(BaseModel):
    """Public receipt scan config (no credentials exposed)."""
    enabled: bool

class ReceiptScanSettings(BaseModel):
    """Full receipt scan settings for admin read/write."""
    enabled: bool
    provider: Optional[Literal["claude", "ollama"]] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    endpoint_url: Optional[str] = None

class CandidateItem(BaseModel):
    """A single item parsed from a receipt by the AI model."""
    item_name: str
    item_type: Literal["food", "household"]
    category_name: Optional[str] = None
    quantity: Decimal = Field(default=Decimal("1"), ge=0)
    unit_name: Optional[str] = None
    notes: Optional[str] = None

class ReceiptScanResponse(BaseModel):
    items: List[CandidateItem]

class BulkItemCreate(BaseModel):
    items: List[ItemCreate]

class BulkItemResult(BaseModel):
    status: int
    item: Optional[ItemOut] = None
    error: Optional[str] = None
