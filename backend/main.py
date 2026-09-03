"""
FastAPI application entry point for the 3D ULPIN prototype.
"""

from fastapi import FastAPI

from backend.app.routers.cadastral import router as cadastral_router


app = FastAPI(
    title="3D ULPIN Cadastral API",
    description=(
        "Prototype API for querying the 3D cadastral model "
        "containing parcels, buildings, floors, property units, "
        "and underground assets."
    ),
    version="0.1.0",
)


app.include_router(cadastral_router)


@app.get("/")
def root():
    return {
        "service": "3D ULPIN Cadastral API",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }