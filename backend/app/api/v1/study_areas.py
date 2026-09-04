import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.parcel import Parcel
from backend.app.models.study_area import StudyArea
from backend.app.schemas.study_area import StudyAreaCreate, StudyAreaResponse


router = APIRouter(
    prefix="/study-areas",
    tags=["Study Areas"]
)


@router.get("/", response_model=list[StudyAreaResponse])
def get_study_areas(db: Session = Depends(get_db)):
    study_areas = db.query(
        StudyArea.id,
        StudyArea.name,
        StudyArea.description,
        func.ST_AsGeoJSON(
            StudyArea.boundary
        ).label("boundary")
    ).all()

    return [
        {
            "id": study_area.id,
            "name": study_area.name,
            "description": study_area.description,
            "boundary": json.loads(study_area.boundary)
        }
        for study_area in study_areas
    ]


@router.post("/", response_model=StudyAreaResponse)
def create_study_area(
    data: StudyAreaCreate,
    db: Session = Depends(get_db)
):
    try:
        boundary = db.execute(
            func.ST_GeomFromGeoJSON(
                json.dumps(data.boundary)
            )
        ).scalar_one()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid GeoJSON boundary"
        )

    study_area = StudyArea(
        name=data.name,
        description=data.description,
        boundary=boundary
    )

    db.add(study_area)
    try:
        db.commit()
    except (IntegrityError, DataError):
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid validation issue"
        )
    db.refresh(study_area)

    geojson = db.query(
        func.ST_AsGeoJSON(StudyArea.boundary)
    ).filter(
        StudyArea.id == study_area.id
    ).scalar()

    return {
        "id": study_area.id,
        "name": study_area.name,
        "description": study_area.description,
        "boundary": json.loads(geojson)
    }


@router.get("/{study_area_id}", response_model=StudyAreaResponse)
def get_study_area(
    study_area_id: int,
    db: Session = Depends(get_db)
):
    study_area = db.query(
        StudyArea.id,
        StudyArea.name,
        StudyArea.description,
        func.ST_AsGeoJSON(
            StudyArea.boundary
        ).label("boundary")
    ).filter(
        StudyArea.id == study_area_id
    ).first()

    if study_area is None:
        raise HTTPException(
            status_code=404,
            detail="Study Area not found"
        )

    return {
        "id": study_area.id,
        "name": study_area.name,
        "description": study_area.description,
        "boundary": json.loads(study_area.boundary)
    }


@router.get("/{study_area_id}/parcels")
def get_study_area_parcels(
    study_area_id: int,
    db: Session = Depends(get_db)
):
    study_area = db.query(StudyArea).filter(
        StudyArea.id == study_area_id
    ).first()

    if study_area is None:
        raise HTTPException(
            status_code=404,
            detail="Study Area not found"
        )

    parcels = db.query(
        Parcel.id,
        Parcel.study_area_id,
        Parcel.parcel_number,
        func.ST_AsGeoJSON(
            Parcel.geometry
        ).label("geometry")
    ).filter(
        Parcel.study_area_id == study_area_id
    ).all()

    return [
        {
            "id": parcel.id,
            "study_area_id": parcel.study_area_id,
            "parcel_number": parcel.parcel_number,
            "geometry": json.loads(parcel.geometry)
        }
        for parcel in parcels
    ]
