from fastapi import FastAPI
from app.api.v1.parcels import router as parcels_router
from app.api.v1.study_areas import router as study_areas_router
from app.api.v1.buildings import router as buildings_router
from app.api.v1.floors import router as floors_router
from app.api.v1.property_units import router as property_units_router
from app.api.v1.ulpins import router as ulpins_router
from app.api.v1.underground_assets import router as underground_assets_router
from app.api.v1.validation_issues import router as validation_issues_router

app = FastAPI(
    title="3D ULPIN Backend",
    version="1.0.0",
    description="Backend API for AI-Assisted 3D ULPIN and Vertical Property Mapping"
)


app.include_router(
    study_areas_router,
    prefix="/api/v1"
)
app.include_router(
    parcels_router,
    prefix="/api/v1"
)

app.include_router(
    buildings_router,
    prefix="/api/v1"
)

app.include_router(
    floors_router,
    prefix="/api/v1"
)

app.include_router(
    property_units_router,
    prefix="/api/v1"
)



app.include_router(
    ulpins_router,
    prefix="/api/v1"
)

app.include_router(
    underground_assets_router,
    prefix="/api/v1"
)


app.include_router(
    validation_issues_router,
    prefix="/api/v1"
)

@app.get("/")
def root():
    return {
        "message": "3D ULPIN Backend is running"
    }