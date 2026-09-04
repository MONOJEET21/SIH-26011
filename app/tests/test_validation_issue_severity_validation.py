from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_invalid_validation_issue_severity_rejected():
    payload = {
        "entity_type": "PROPERTY_UNIT",
        "entity_id": 1,
        "issue_type": "TEST_ISSUE",
        "message": "Test invalid severity",
        "severity": "INVALID",
        "geometry": {
            "type": "Point",
            "coordinates": [91.8, 26.1]
        }
    }

    response = client.post("/api/v1/validation-issues/", json=payload)

    assert response.status_code == 400