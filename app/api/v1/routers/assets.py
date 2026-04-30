import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.db.models import Asset
from app.schemas.asset import (
    AssetCreate,
    AssetListResponse,
    AssetRead,
    AssetStatus,
    AssetStatusUpdate,
    AssetUpdate,
)
from app.services.asset_service import can_transition

router = APIRouter()


@router.get("", response_model=AssetListResponse)
def list_assets(
    q: str | None = Query(default=None, description="Search asset tag, name, serial"),
    status: AssetStatus | None = Query(default=None),
    category: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AssetListResponse:
    query = db.query(Asset)

    if q:
        like = f"%{q}%"
        query = query.filter(
            Asset.asset_tag.ilike(like)
            | Asset.name.ilike(like)
            | Asset.serial_no.ilike(like)
            | Asset.brand.ilike(like)
        )
    if status:
        query = query.filter(Asset.status == status.value)
    if category:
        query = query.filter(Asset.category == category)

    total = query.count()
    assets = query.order_by(Asset.id.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return AssetListResponse(
        items=[AssetRead.model_validate(a) for a in assets],
        total=total,
        page=page,
        per_page=per_page,
        pages=max(1, math.ceil(total / per_page)),
    )


@router.post("", response_model=AssetRead, status_code=201)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db)) -> AssetRead:
    if db.query(Asset).filter(Asset.asset_tag == payload.asset_tag).first():
        raise HTTPException(status_code=400, detail="Asset tag already exists")

    asset = Asset(**payload.model_dump(), status=AssetStatus.IN_STOCK.value)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return AssetRead.model_validate(asset)


@router.get("/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: int, db: Session = Depends(get_db)) -> AssetRead:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetRead.model_validate(asset)


@router.put("/{asset_id}", response_model=AssetRead)
def update_asset(asset_id: int, payload: AssetUpdate, db: Session = Depends(get_db)) -> AssetRead:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)

    db.commit()
    db.refresh(asset)
    return AssetRead.model_validate(asset)


@router.delete("/{asset_id}", status_code=204)
def delete_asset(asset_id: int, db: Session = Depends(get_db)) -> None:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    db.delete(asset)
    db.commit()


@router.post("/{asset_id}/status", response_model=AssetRead)
def update_asset_status(asset_id: int, payload: AssetStatusUpdate, db: Session = Depends(get_db)) -> AssetRead:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
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
