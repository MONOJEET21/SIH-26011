import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import DataError,IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.parcel import Parcel
from app.models.study_area import StudyArea
from app.schemas.parcel import ParcelCreate, ParcelResponse
from app.models.building import Building


router = APIRouter(
    prefix="/parcels",
    tags=["Parcels"]
)


@router.get("/", response_model=list[ParcelResponse])
def get_parcels(db: Session = Depends(get_db)):
    parcels = db.query(
        Parcel.id,
        Parcel.study_area_id,
        Parcel.parcel_number,
        Parcel.parcel_code,
        Parcel.area,
        Parcel.land_use,
        Parcel.status,
        func.ST_AsGeoJSON(Parcel.geometry).label("geometry")
    ).all()

    return [
        {
            "id": parcel.id,
            "study_area_id": parcel.study_area_id,
            "parcel_number": parcel.parcel_number,
            "parcel_code": parcel.parcel_code,
            "area": parcel.area,
            "land_use": parcel.land_use,
            "status": parcel.status,
            "geometry": json.loads(parcel.geometry)
        }
        for parcel in parcels
    ]


@router.post("/", response_model=dict)
def create_parcel(
    data: ParcelCreate,
    db: Session = Depends(get_db)
):
    study_area = db.query(StudyArea).filter(
        StudyArea.id == data.study_area_id
    ).first()

    if study_area is None:
        raise HTTPException(
            status_code=404,
            detail="Study area not found"
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

    parcel = Parcel(
        study_area_id=data.study_area_id,
        parcel_number=data.parcel_number,
        parcel_code=data.parcel_code,
        area=data.area,
        land_use=data.land_use,
        status=data.status,
        geometry=geometry
    )

    db.add(parcel)

    try:
        db.commit()
    except (IntegrityError, DataError):
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid parcel data"
        )

    db.refresh(parcel)

    geometry = db.execute(
        select(func.ST_AsGeoJSON(parcel.geometry))
    ).scalar_one()

    return {
        "id": parcel.id,
        "study_area_id": parcel.study_area_id,
        "parcel_number": parcel.parcel_number,
        "parcel_code": parcel.parcel_code,
        "area": parcel.area,
        "land_use": parcel.land_use,
        "status": parcel.status,
        "geometry": json.loads(geometry)
    }

@router.get("/{parcel_id}/buildings")
def get_parcel_buildings(
    parcel_id: int,
    db: Session = Depends(get_db)
):
    parcel = db.query(Parcel).filter(
        Parcel.id == parcel_id
    ).first()

    if parcel is None:
        raise HTTPException(
            status_code=404,
            detail="Parcel not found"
        )

    buildings = db.query(
        Building.id,
        Building.parcel_id,
        Building.building_number,
        Building.building_code,
        Building.ground_elevation,
        Building.height,
        Building.floor_count,
        Building.building_type,
        Building.status,
        func.ST_AsGeoJSON(Building.geometry).label("geometry")
    ).filter(
        Building.parcel_id == parcel_id
    ).all()

    return [
        {
            "id": building.id,
            "parcel_id": building.parcel_id,
            "building_number": building.building_number,
            "building_code": building.building_code,
            "ground_elevation": building.ground_elevation,
            "height": building.height,
            "floor_count": building.floor_count,
            "building_type": building.building_type,
            "status": building.status,
            "geometry": json.loads(building.geometry)
        }
        for building in buildings
    ]