from pydantic import BaseModel


class FloorCreate(BaseModel):
    building_id: int
    level_number: int
    z_min: float
    z_max: float
    geometry: dict


class FloorResponse(BaseModel):
    id: int
    building_id: int
    level_number: int
    z_min: float
    z_max: float
    geometry: dict