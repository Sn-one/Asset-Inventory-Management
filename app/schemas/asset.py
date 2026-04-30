from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AssetStatus(StrEnum):
    IN_STOCK = "in_stock"
    ASSIGNED = "assigned"
    IN_REPAIR = "in_repair"
    RETIRED = "retired"
    DISPOSED = "disposed"


CATEGORIES = [
    "Laptop", "Desktop", "Monitor", "Printer", "Phone",
    "Tablet", "Server", "Networking", "Peripheral", "Other",
]


class AssetCreate(BaseModel):
    asset_tag: str = Field(min_length=1, max_length=64)
    name: str | None = Field(default=None, max_length=128)
    brand: str | None = Field(default=None, max_length=64)
    model_no: str | None = Field(default=None, max_length=128)
    serial_no: str | None = Field(default=None, max_length=128)
    category: str | None = Field(default=None, max_length=64)
    department: str | None = Field(default=None, max_length=64)
    location: str | None = Field(default=None, max_length=64)
    assigned_to: str | None = Field(default=None, max_length=128)
    purchase_date: date | None = None
    purchase_cost: float | None = Field(default=None, ge=0)
    warranty_expiry: date | None = None
    notes: str | None = None


class AssetUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    brand: str | None = Field(default=None, max_length=64)
    model_no: str | None = Field(default=None, max_length=128)
    serial_no: str | None = Field(default=None, max_length=128)
    category: str | None = Field(default=None, max_length=64)
    department: str | None = Field(default=None, max_length=64)
    location: str | None = Field(default=None, max_length=64)
    assigned_to: str | None = Field(default=None, max_length=128)
    purchase_date: date | None = None
    purchase_cost: float | None = Field(default=None, ge=0)
    warranty_expiry: date | None = None
    notes: str | None = None


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_tag: str
    name: str | None = None
    brand: str | None = None
    model_no: str | None = None
    serial_no: str | None = None
    category: str | None = None
    department: str | None = None
    location: str | None = None
    assigned_to: str | None = None
    purchase_date: date | None = None
    purchase_cost: float | None = None
    warranty_expiry: date | None = None
    notes: str | None = None
    status: AssetStatus
    created_at: datetime
    updated_at: datetime


class AssetStatusUpdate(BaseModel):
    status: AssetStatus


class AssetListResponse(BaseModel):
    items: list[AssetRead]
    total: int
    page: int
    per_page: int
    pages: int
