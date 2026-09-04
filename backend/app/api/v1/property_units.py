import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import DataError,IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.floor import Floor
from backend.app.models.property_unit import PropertyUnit
from backend.app.schemas.property_unit import PropertyUnitCreate, PropertyUnitResponse




router = APIRouter(
    prefix="/property-units",
    tags=["Property Units"]
)


@router.get("/", response_model=list[PropertyUnitResponse])
def get_property_units(
    db: Session = Depends(get_db)
):
    units = db.query(
        PropertyUnit.id,
        PropertyUnit.floor_id,
        PropertyUnit.unit_code,
        PropertyUnit.unit_number,
        PropertyUnit.unit_type,
        PropertyUnit.area,
        PropertyUnit.volume,
        PropertyUnit.ownership_status,
        PropertyUnit.status,
        func.ST_AsGeoJSON(PropertyUnit.geometry).label("geometry")
    ).all()

    return [
        {
            "id": unit.id,
            "floor_id": unit.floor_id,
            "unit_code": unit.unit_code,
            "unit_number": unit.unit_number,
            "unit_type": unit.unit_type,
            "area": unit.area,
            "volume": unit.volume,
            "ownership_status": unit.ownership_status,
            "status": unit.status,
            "geometry": json.loads(unit.geometry)
        }
        for unit in units
    ]


@router.post("/", response_model=dict)
def create_property_unit(
    data: PropertyUnitCreate,
    db: Session = Depends(get_db)
):
    floor = db.query(Floor).filter(
        Floor.id == data.floor_id
    ).first()

    if floor is None:
        raise HTTPException(
            status_code=404,
            detail="Floor not found"
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

    unit = PropertyUnit(
        floor_id=data.floor_id,
        unit_code=data.unit_code,
        unit_number=data.unit_number,
        unit_type=data.unit_type,
        area=data.area,
        volume=data.volume,
        ownership_status=data.ownership_status,
        status=data.status,
        geometry=geometry
    )

    db.add(unit)
    
    try:
        db.commit()
    except (IntegrityError, DataError):
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid property unit data"
        )
    
    db.refresh(unit)

    geometry = db.execute(
        select(
            func.ST_AsGeoJSON(unit.geometry)
        )
    ).scalar_one()

    return {
        "id": unit.id,
        "floor_id": unit.floor_id,
        "unit_code": unit.unit_code,
        "unit_number": unit.unit_number,
        "unit_type": unit.unit_type,
        "area": unit.area,
        "volume": unit.volume,
        "ownership_status": unit.ownership_status,
        "status": unit.status,
        "geometry": json.loads(geometry)
    }
