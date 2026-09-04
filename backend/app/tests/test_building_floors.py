from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_building_floors():
    response = client.get("/api/v1/buildings/1/floors")

    assert response.status_code == 200
    assert isinstance(response.json(), list)