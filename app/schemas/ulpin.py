from pydantic import BaseModel


class ULPINCreate(BaseModel):
    ulpin: str
    entity_type: str
    entity_id: int
    parent_ulpin: str | None = None
    hierarchy_path: str | None = None
    status: str = "ACTIVE"


class ULPINResponse(BaseModel):
    id: int
    ulpin: str
    entity_type: str
    entity_id: int
    parent_ulpin: str | None = None
    hierarchy_path: str | None = None
    status: str

class ULPINPropertyRecordResponse(BaseModel):
    ulpin: ULPINResponse

    property_unit: dict
    floor: dict
    building: dict
    parcel: dict
    study_area: dict

    property_unit_geometry: dict | None = None
    floor_geometry: dict | None = None
    building_geometry: dict | None = None
    parcel_geometry: dict | None = None
    study_area_geometry: dict | None = None