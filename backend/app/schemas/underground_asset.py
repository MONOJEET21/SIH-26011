from pydantic import BaseModel


class UndergroundAssetCreate(BaseModel):
    parcel_id: int
    asset_type: str
    asset_code: str
    z_min: float
    z_max: float
    depth: float
    status: str = "ACTIVE"
    geometry: dict


class UndergroundAssetResponse(BaseModel):
    id: int
    parcel_id: int
    asset_type: str
    asset_code: str
    z_min: float
    z_max: float
    depth: float
    status: str
    geometry: dict
