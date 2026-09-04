from pydantic import BaseModel


class ParcelCreate(BaseModel):
    study_area_id: int
    parcel_number: str
    parcel_code: str
    area: float
    land_use: str
    status: str = "ACTIVE"
    geometry: dict


class ParcelResponse(BaseModel):
    id: int
    study_area_id: int
    parcel_number: str
    parcel_code: str
    area: float
    land_use: str
    status: str
    geometry: dict
