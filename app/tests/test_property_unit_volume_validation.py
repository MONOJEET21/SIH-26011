from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_negative_property_unit_volume_rejected():
    payload = {
        "floor_id": 1,
        "unit_code": "TEST-NEGATIVE-VOLUME-PYTEST",
        "unit_number": "TEST-NEGATIVE-VOLUME-PYTEST",
        "unit_type": "RESIDENTIAL",
        "area": 100,
        "volume": -10,
        "ownership_status": "OWNED",
        "status": "ACTIVE",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [91.8, 26.1],
                [91.81, 26.1],
                [91.81, 26.11],
                [91.8, 26.11],
                [91.8, 26.1]
            ]]
        }
    }

    response = client.post("/api/v1/property-units/", json=payload)

    assert response.status_code == 400