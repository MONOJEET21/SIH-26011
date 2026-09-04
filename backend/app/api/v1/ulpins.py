import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import DataError,IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.ulpin import ULPIN
from app.models.property_unit import PropertyUnit
from app.models.floor import Floor
from app.models.building import Building
from app.models.parcel import Parcel
from app.models.study_area import StudyArea

from app.schemas.ulpin import (
    ULPINCreate,
    ULPINResponse,
    ULPINPropertyRecordResponse
)


router = APIRouter(
    prefix="/ulpins",
    tags=["ULPINs"]
)


@router.get("/", response_model=list[ULPINResponse])
def get_ulpins(
    db: Session = Depends(get_db)
):
    return db.query(ULPIN).all()


@router.post("/", response_model=ULPINResponse)
def create_ulpin(
    data: ULPINCreate,
    db: Session = Depends(get_db)
):

    existing_ulpin = db.query(ULPIN).filter(
        ULPIN.ulpin == data.ulpin
    ).first()

    if existing_ulpin is not None:
        raise HTTPException(
            status_code=409,
            detail="ULPIN already exists"
        )

    ulpin = ULPIN(
        ulpin=data.ulpin,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        parent_ulpin=data.parent_ulpin,
        hierarchy_path=data.hierarchy_path,
        status=data.status
    )

    db.add(ulpin)
    try:
        db.commit()
    except (IntegrityError, DataError):
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid ulpin data"
        )
    db.refresh(ulpin)

    return ulpin


@router.get(
    "/{ulpin}",
    response_model=ULPINPropertyRecordResponse
)
def get_ulpin(
    ulpin: str,
    db: Session = Depends(get_db)
):
    item = db.query(ULPIN).filter(
        ULPIN.ulpin == ulpin
    ).first()

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="ULPIN not found"
        )

    # Currently support PROPERTY_UNIT ULPINs.
    if item.entity_type != "PROPERTY_UNIT":
        raise HTTPException(
            status_code=400,
            detail="Complete property record is currently supported for PROPERTY_UNIT ULPINs only"
        )

    property_unit = db.query(PropertyUnit).filter(
        PropertyUnit.id == item.entity_id
    ).first()

    if property_unit is None:
        raise HTTPException(
            status_code=404,
            detail="Property unit linked to ULPIN not found"
        )

    floor = db.query(Floor).filter(
        Floor.id == property_unit.floor_id
    ).first()

    if floor is None:
        raise HTTPException(
            status_code=404,
            detail="Floor linked to property unit not found"
        )

    building = db.query(Building).filter(
        Building.id == floor.building_id
    ).first()

    if building is None:
        raise HTTPException(
            status_code=404,
            detail="Building linked to floor not found"
        )

    parcel = db.query(Parcel).filter(
        Parcel.id == building.parcel_id
    ).first()

    if parcel is None:
        raise HTTPException(
            status_code=404,
            detail="Parcel linked to building not found"
        )

    study_area = db.query(StudyArea).filter(
        StudyArea.id == parcel.study_area_id
    ).first()

    if study_area is None:
        raise HTTPException(
            status_code=404,
            detail="Study area linked to parcel not found"
        )

    property_unit_geometry = db.execute(
        select(func.ST_AsGeoJSON(property_unit.geometry))
    ).scalar_one()

    floor_geometry = db.execute(
        select(func.ST_AsGeoJSON(floor.geometry))
    ).scalar_one()

    building_geometry = db.execute(
        select(func.ST_AsGeoJSON(building.geometry))
    ).scalar_one()

    parcel_geometry = db.execute(
        select(func.ST_AsGeoJSON(parcel.geometry))
    ).scalar_one()

    study_area_geometry = db.execute(
        select(func.ST_AsGeoJSON(study_area.boundary))
    ).scalar_one()

    return {
        "ulpin": item,
        "property_unit": {
            "id": property_unit.id,
            "floor_id": property_unit.floor_id,
            "unit_code": property_unit.unit_code,
            "unit_number": property_unit.unit_number,
            "unit_type": property_unit.unit_type,
            "area": property_unit.area,
            "volume": property_unit.volume,
            "ownership_status": property_unit.ownership_status,
            "status": property_unit.status
        },
        "floor": {
            "id": floor.id,
            "building_id": floor.building_id,
            "level_number": floor.level_number,
            "z_min": floor.z_min,
            "z_max": floor.z_max
        },
        "building": {
            "id": building.id,
            "parcel_id": building.parcel_id,
            "building_number": building.building_number,
            "building_code": building.building_code,
            "ground_elevation": building.ground_elevation,
            "height": building.height,
            "floor_count": building.floor_count,
            "building_type": building.building_type,
            "status": building.status
        },
        "parcel": {
            "id": parcel.id,
            "study_area_id": parcel.study_area_id,
            "parcel_number": parcel.parcel_number,
            "parcel_code": parcel.parcel_code,
            "area": parcel.area,
            "land_use": parcel.land_use,
            "status": parcel.status
        },
        "study_area": {
            "id": study_area.id,
            "name": study_area.name,
            "description": study_area.description
        },

        "property_unit_geometry": json.loads(property_unit_geometry),
        "floor_geometry": json.loads(floor_geometry),
        "building_geometry": json.loads(building_geometry),
        "parcel_geometry": json.loads(parcel_geometry),
        "study_area_geometry": json.loads(study_area_geometry)
    }