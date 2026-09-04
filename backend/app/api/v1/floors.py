import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.building import Building
from backend.app.db.database import get_db
from backend.app.models.floor import Floor
from backend.app.schemas.floor import FloorCreate, FloorResponse
from backend.app.models.property_unit import PropertyUnit

router = APIRouter(
    prefix="/floors",
    tags=["Floors"]
)


@router.get("/", response_model=list[FloorResponse])
def get_floors(db: Session = Depends(get_db)):

    floors = db.query(
        Floor.id,
        Floor.building_id,
        Floor.level_number,
        Floor.z_min,
        Floor.z_max,
        func.ST_AsGeoJSON(
            Floor.geometry
        ).label("geometry")
    ).all()

    return [
        {
            "id": floor.id,
            "building_id": floor.building_id,
            "level_number": floor.level_number,
            "z_min": floor.z_min,
            "z_max": floor.z_max,
            "geometry": json.loads(floor.geometry)
        }
        for floor in floors
    ]


@router.post("/")
def create_floor(
    data: FloorCreate,
    db: Session = Depends(get_db)
):
    building = db.query(Building).filter(
        Building.id == data.building_id
    ).first()

    if building is None:
        raise HTTPException(
            status_code=404,
            detail="Building not found"
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

    floor = Floor(
        building_id=data.building_id,
        level_number=data.level_number,
        z_min=data.z_min,
        z_max=data.z_max,
        geometry=geometry
    )

    db.add(floor)
    db.commit()
    db.refresh(floor)

    geometry = db.query(
        func.ST_AsGeoJSON(
            Floor.geometry
        )
    ).filter(
        Floor.id == floor.id
    ).scalar()

    return {
        "id": floor.id,
        "building_id": floor.building_id,
        "level_number": floor.level_number,
        "z_min": floor.z_min,
        "z_max": floor.z_max,
        "geometry": json.loads(geometry)
    }


@router.get("/{floor_id}/property-units")
def get_floor_property_units(
    floor_id: int,
    db: Session = Depends(get_db)
):
    floor = db.query(Floor).filter(
        Floor.id == floor_id
    ).first()

    if floor is None:
        raise HTTPException(
            status_code=404,
            detail="Floor not found"
        )

    units = db.query(
        PropertyUnit.id,
        PropertyUnit.floor_id,
        PropertyUnit.unit_number,
        PropertyUnit.unit_type,
        func.ST_AsGeoJSON(
            PropertyUnit.geometry
        ).label("geometry")
    ).filter(
        PropertyUnit.floor_id == floor_id
    ).all()

    return [
        {
            "id": unit.id,
            "floor_id": unit.floor_id,
            "unit_number": unit.unit_number,
            "unit_type": unit.unit_type,
            "geometry": json.loads(unit.geometry)
        }
        for unit in units
    ]


@router.get("/{floor_id}/units")
def get_floor_units(
    floor_id: int,
    db: Session = Depends(get_db)
):
    floor = db.query(Floor).filter(
        Floor.id == floor_id
    ).first()

    if floor is None:
        raise HTTPException(
            status_code=404,
            detail="Floor not found"
        )

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
    ).filter(
        PropertyUnit.floor_id == floor_id
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
