from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_study_area_parcels():
    response = client.get("/api/v1/study-areas/6/parcels")

    assert response.status_code == 200
    assert isinstance(response.json(), list)