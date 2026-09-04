import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import DataError,IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.building import Building
from app.models.parcel import Parcel
from app.schemas.building import BuildingCreate, BuildingResponse
from app.models.floor import Floor


router = APIRouter(
    prefix="/buildings",
    tags=["Buildings"]
)


@router.get("/", response_model=list[BuildingResponse])
def get_buildings(db: Session = Depends(get_db)):
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


@router.post("/", response_model=dict)
def create_building(
    data: BuildingCreate,
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

    building = Building(
        parcel_id=data.parcel_id,
        building_number=data.building_number,
        building_code=data.building_code,
        ground_elevation=data.ground_elevation,
        height=data.height,
        floor_count=data.floor_count,
        building_type=data.building_type,
        status=data.status,
        geometry=geometry
    )

    db.add(building)
    
    try:
        db.commit()
    except (IntegrityError, DataError):
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid building data"
        )
    db.refresh(building)

    geometry = db.execute(
        select(func.ST_AsGeoJSON(building.geometry))
    ).scalar_one()

    return {
        "id": building.id,
        "parcel_id": building.parcel_id,
        "building_number": building.building_number,
        "building_code": building.building_code,
        "ground_elevation": building.ground_elevation,
        "height": building.height,
        "floor_count": building.floor_count,
        "building_type": building.building_type,
        "status": building.status,
        "geometry": json.loads(geometry)
    }

@router.get("/{building_id}/floors")
def get_building_floors(
    building_id: int,
    db: Session = Depends(get_db)
):
    building = db.query(Building).filter(
        Building.id == building_id
    ).first()

    if building is None:
        raise HTTPException(
            status_code=404,
            detail="Building not found"
        )

    floors = db.query(
        Floor.id,
        Floor.building_id,
        Floor.level_number,
        Floor.z_min,
        Floor.z_max,
        func.ST_AsGeoJSON(Floor.geometry).label("geometry")
    ).filter(
        Floor.building_id == building_id
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