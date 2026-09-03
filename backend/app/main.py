from fastapi import FastAPI

from backend.app.routers.cadastral import router as cadastral_router


app = FastAPI(
    title="3D ULPIN Cadastral API",
    description="Prototype API for the 3D cadastral model.",
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
        "status": "healthy"
    }