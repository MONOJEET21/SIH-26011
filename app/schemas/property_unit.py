from pydantic import BaseModel


class PropertyUnitCreate(BaseModel):
    floor_id: int
    unit_code: str
    unit_number: str
    unit_type: str
    area: float
    volume: float
    ownership_status: str
    status: str = "ACTIVE"
    geometry: dict


class PropertyUnitResponse(BaseModel):
    id: int
    floor_id: int
    unit_code: str
    unit_number: str
    unit_type: str
    area: float
    volume: float
    ownership_status: str
    status: str
    geometry: dict