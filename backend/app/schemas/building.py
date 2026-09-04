from pydantic import BaseModel


class BuildingCreate(BaseModel):
    parcel_id: int
    building_number: str
    building_code: str
    ground_elevation: float
    height: float
    floor_count: int
    building_type: str
    status: str = "ACTIVE"
    geometry: dict


class BuildingResponse(BaseModel):
    id: int
    parcel_id: int
    building_number: str
    building_code: str
    ground_elevation: float
    height: float
    floor_count: int
    building_type: str
    status: str
    geometry: dict
