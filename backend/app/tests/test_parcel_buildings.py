from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_parcel_buildings():
    response = client.get("/api/v1/parcels/1/buildings")

    assert response.status_code == 200
    assert isinstance(response.json(), list)