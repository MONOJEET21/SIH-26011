from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_underground_assets():
    response = client.get(
        "/api/v1/underground-assets/"
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)