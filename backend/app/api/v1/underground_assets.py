import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import DataError,IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.parcel import Parcel
from backend.app.models.underground_asset import UndergroundAsset
from backend.app.schemas.underground_asset import (
    UndergroundAssetCreate,
    UndergroundAssetResponse
)

router = APIRouter(
    prefix="/underground-assets",
    tags=["Underground Assets"]
)


@router.get("/", response_model=list[UndergroundAssetResponse])
def get_underground_assets(
    db: Session = Depends(get_db)
):
    assets = db.query(
        UndergroundAsset.id,
        UndergroundAsset.parcel_id,
        UndergroundAsset.asset_type,
        UndergroundAsset.asset_code,
        UndergroundAsset.z_min,
        UndergroundAsset.z_max,
        UndergroundAsset.depth,
        UndergroundAsset.status,
        func.ST_AsGeoJSON(
            UndergroundAsset.geometry
        ).label("geometry")
    ).all()

    return [
        {
            "id": asset.id,
            "parcel_id": asset.parcel_id,
            "asset_type": asset.asset_type,
            "asset_code": asset.asset_code,
            "z_min": asset.z_min,
            "z_max": asset.z_max,
            "depth": asset.depth,
            "status": asset.status,
            "geometry": json.loads(asset.geometry)
        }
        for asset in assets
    ]


@router.post("/", response_model=dict)
def create_underground_asset(
    data: UndergroundAssetCreate,
    db: Session = Depends(get_db)
):
    parcel = db.query(Parcel).filter(
        Parcel.id == data.parcel_id
    ).first()

    if parcel is None:
        raise HTTPException(
            status_code=404,
            detail="Parcel not found"
        )

    if data.z_min >= data.z_max:
        raise HTTPException(
            status_code=400,
            detail="z_min must be less than z_max"
        )

    try:
        geometry = db.execute(
            func.ST_GeomFromGeoJSON(
                json.dumps(data.geometry)
            )
        ).scalar_one()

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid GeoJSON geometry"
        )

    asset = UndergroundAsset(
        parcel_id=data.parcel_id,
        asset_type=data.asset_type,
        asset_code=data.asset_code,
        z_min=data.z_min,
        z_max=data.z_max,
        depth=data.depth,
        status=data.status,
        geometry=geometry
    )

    db.add(asset)
    try:

        db.commit()
    except (IntegrityError, DataError):
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid Underground asset data"
        )
    db.refresh(asset)
        

    

    geometry = db.execute(
        select(
            func.ST_AsGeoJSON(asset.geometry)
        )
    ).scalar_one()

    return {
        "id": asset.id,
        "parcel_id": asset.parcel_id,
        "asset_type": asset.asset_type,
        "asset_code": asset.asset_code,
        "z_min": asset.z_min,
        "z_max": asset.z_max,
        "depth": asset.depth,
        "status": asset.status,
        "geometry": json.loads(geometry)
    }
