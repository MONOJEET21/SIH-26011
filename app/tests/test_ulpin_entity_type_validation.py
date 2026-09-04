from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_invalid_ulpin_entity_type_rejected():
    payload = {
        "ulpin": "ULPIN-PYTEST-INVALID-TYPE",
        "entity_type": "INVALID_TYPE",
        "entity_id": 1,
        "parent_ulpin": None,
        "hierarchy_path": None,
        "status": "ACTIVE"
    }

    response = client.post("/api/v1/ulpins/", json=payload)

    assert response.status_code == 400