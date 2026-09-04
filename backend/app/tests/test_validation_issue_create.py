from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_validation_issue():
    response = client.post(
        "/api/v1/validation-issues/",
        json={
            "entity_type": "PROPERTY_UNIT",
            "entity_id": 1,
            "issue_type": "INVALID_GEOMETRY",
            "message": "Pytest validation issue",
            "severity": "HIGH",
            "geometry": {
                "type": "Point",
                "coordinates": [91.755, 26.162]
            }
        }
    )

    assert response.status_code == 200