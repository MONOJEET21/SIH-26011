from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_duplicate_ulpin():
    response = client.post(
        "/api/v1/ulpins/",
        json={
            "ulpin": "ULPIN-ASSAM-000002",
            "entity_type": "PROPERTY_UNIT",
            "entity_id": 5,
            "parent_ulpin": None,
            "hierarchy_path": "PROPERTY_UNIT/5",
            "status": "ACTIVE"
        }
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "ULPIN already exists"