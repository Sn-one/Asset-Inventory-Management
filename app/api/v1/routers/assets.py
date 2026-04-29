from fastapi import APIRouter, HTTPException

from app.schemas.asset import AssetCreate, AssetRead, AssetStatus, AssetStatusUpdate
from app.services.asset_service import can_transition

router = APIRouter()
_ASSETS: dict[int, AssetRead] = {}
_NEXT_ID = 1


def reset_asset_store() -> None:
    global _NEXT_ID
    _ASSETS.clear()
    _NEXT_ID = 1


@router.get("", response_model=dict[str, list[AssetRead]])
def list_assets() -> dict[str, list[AssetRead]]:
    return {"items": list(_ASSETS.values())}


@router.post("", response_model=AssetRead, status_code=201)
def create_asset(payload: AssetCreate) -> AssetRead:
    global _NEXT_ID
    asset = AssetRead(id=_NEXT_ID, status=AssetStatus.IN_STOCK, **payload.model_dump())
    _ASSETS[_NEXT_ID] = asset
    _NEXT_ID += 1
    return asset


@router.post("/{asset_id}/status", response_model=AssetRead)
def update_asset_status(asset_id: int, payload: AssetStatusUpdate) -> AssetRead:
    asset = _ASSETS.get(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not can_transition(asset.status, payload.status):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {asset.status} to {payload.status}",
        )

    updated = asset.model_copy(update={"status": payload.status})
    _ASSETS[asset_id] = updated
    return updated
from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_assets() -> dict[str, list]:
    return {"items": []}
