from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Asset
from app.db.session import SessionLocal
from app.schemas.asset import AssetCreate, AssetRead, AssetStatus, AssetStatusUpdate
from app.services.asset_service import can_transition

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=dict[str, list[AssetRead]])
def list_assets(db: Session = Depends(get_db)) -> dict[str, list[AssetRead]]:
    assets = db.query(Asset).all()
    return {"items": [AssetRead.model_validate(asset) for asset in assets]}


@router.post("", response_model=AssetRead, status_code=201)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db)) -> AssetRead:
    # Check if asset_tag already exists
    existing = db.query(Asset).filter(Asset.asset_tag == payload.asset_tag).first()
    if existing:
        raise HTTPException(status_code=400, detail="Asset tag already exists")
    
    asset = Asset(
        asset_tag=payload.asset_tag,
        serial_no=payload.serial_no,
        category=payload.category,
        location=payload.location,
        status=AssetStatus.IN_STOCK.value
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return AssetRead.model_validate(asset)


@router.post("/{asset_id}/status", response_model=AssetRead)
def update_asset_status(asset_id: int, payload: AssetStatusUpdate, db: Session = Depends(get_db)) -> AssetRead:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not can_transition(AssetStatus(asset.status), payload.status):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {asset.status} to {payload.status.value}",
        )

    asset.status = payload.status.value
    db.commit()
    db.refresh(asset)
    return AssetRead.model_validate(asset)
