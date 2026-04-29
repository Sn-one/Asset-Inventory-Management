from enum import StrEnum

from pydantic import BaseModel, Field


class AssetStatus(StrEnum):
    IN_STOCK = "in_stock"
    ASSIGNED = "assigned"
    IN_REPAIR = "in_repair"
    RETIRED = "retired"
    DISPOSED = "disposed"


class AssetCreate(BaseModel):
    asset_tag: str = Field(min_length=1, max_length=64)
    serial_no: str | None = Field(default=None, max_length=128)
    category: str | None = Field(default=None, max_length=64)
    location: str | None = Field(default=None, max_length=64)


class AssetRead(BaseModel):
    id: int
    asset_tag: str
    serial_no: str | None = None
    category: str | None = None
    location: str | None = None
    status: AssetStatus


class AssetStatusUpdate(BaseModel):
    status: AssetStatus
