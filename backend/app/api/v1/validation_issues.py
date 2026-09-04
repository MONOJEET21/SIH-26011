import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import DataError,IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.property_unit import PropertyUnit
from backend.app.models.validation_issue import ValidationIssue
from backend.app.schemas.validation_issue import (
    ValidationIssueCreate,
    ValidationIssueResponse
)

router = APIRouter(
    prefix="/validation-issues",
    tags=["Validation Issues"]
)


@router.get("/", response_model=list[ValidationIssueResponse])
def get_validation_issues(
    db: Session = Depends(get_db)
):
    issues = db.query(
        ValidationIssue.id,
        ValidationIssue.entity_type,
        ValidationIssue.entity_id,
        ValidationIssue.issue_type,
        ValidationIssue.message,
        ValidationIssue.severity,
        ValidationIssue.status,
        func.ST_AsGeoJSON(
            ValidationIssue.geometry
        ).label("geometry")
    ).all()

    return [
        {
            "id": issue.id,
            "entity_type": issue.entity_type,
            "entity_id": issue.entity_id,
            "issue_type": issue.issue_type,
            "message": issue.message,
            "severity": issue.severity,
            "status": issue.status,
            "geometry": (
                json.loads(issue.geometry)
                if issue.geometry is not None
                else None
            )
        }
        for issue in issues
    ]


@router.post("/", response_model=dict)
def create_validation_issue(
    data: ValidationIssueCreate,
    db: Session = Depends(get_db)
):
    if data.entity_type == "PROPERTY_UNIT":
        entity = db.query(PropertyUnit).filter(
            PropertyUnit.id == data.entity_id
        ).first()

        if entity is None:
            raise HTTPException(
                status_code=404,
                detail="Property Unit not found"
            )

    geometry = None

    if data.geometry is not None:
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

    issue = ValidationIssue(
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        issue_type=data.issue_type,
        message=data.message,
        severity=data.severity,
        geometry=geometry
    )

    db.add(issue)
    try:
        db.commit()
    except (IntegrityError, DataError):
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid validation issue"
        )
    db.refresh(issue)

    geometry_json = None

    if issue.geometry is not None:
        geometry_json = db.execute(
            select(
                func.ST_AsGeoJSON(issue.geometry)
            )
        ).scalar_one()

        geometry_json = json.loads(geometry_json)

    return {
        "id": issue.id,
        "entity_type": issue.entity_type,
        "entity_id": issue.entity_id,
        "issue_type": issue.issue_type,
        "message": issue.message,
        "severity": issue.severity,
        "status": issue.status,
        "geometry": geometry_json
    }
