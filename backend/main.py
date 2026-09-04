from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# =========================================================
# EXISTING CADASTRAL QUERY API
# =========================================================

from backend.app.routers.cadastral import router as cadastral_router


# =========================================================
# MEMBER 2 DATABASE APIs
# =========================================================

from backend.app.api.v1.parcels import router as parcels_router
from backend.app.api.v1.study_areas import router as study_areas_router
from backend.app.api.v1.buildings import router as buildings_router
from backend.app.api.v1.floors import router as floors_router
from backend.app.api.v1.property_units import (
    router as property_units_router,
)
from backend.app.api.v1.ulpins import router as ulpins_router
from backend.app.api.v1.underground_assets import (
    router as underground_assets_router,
)
from backend.app.api.v1.validation_issues import (
    router as validation_issues_router,
)


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="3D ULPIN Backend",
    description=(
        "Backend API for AI-Assisted 3D ULPIN and "
        "Vertical Property Mapping"
    ),
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# EXISTING TEAM CADASTRAL API
# =========================================================

app.include_router(cadastral_router)


# =========================================================
# MEMBER 2 DATABASE APIs
# =========================================================

app.include_router(
    study_areas_router,
    prefix="/api/v1",
)

app.include_router(
    parcels_router,
    prefix="/api/v1",
)

app.include_router(
    buildings_router,
    prefix="/api/v1",
)

app.include_router(
    floors_router,
    prefix="/api/v1",
)

app.include_router(
    property_units_router,
    prefix="/api/v1",
)

app.include_router(
    ulpins_router,
    prefix="/api/v1",
)

app.include_router(
    underground_assets_router,
    prefix="/api/v1",
)

app.include_router(
    validation_issues_router,
    prefix="/api/v1",
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "service": "3D ULPIN Backend",
        "status": "running",
        "version": "1.0.0",
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
    }