from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_floor_units():
    response = client.get("/api/v1/floors/1/units")

    assert response.status_code == 200
    assert isinstance(response.json(), list)