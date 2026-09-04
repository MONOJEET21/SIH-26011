from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_property_unit():
    response = client.post(
        "/api/v1/property-units/",
        json={
            "floor_id": 1,
            "unit_code": "PYTEST-UNIT-001",
            "unit_number": "PY-101",
            "unit_type": "Residential",
            "area": 85.5,
            "volume": 256.5,
            "ownership_status": "PRIVATE",
            "status": "ACTIVE",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [91.74, 26.14],
                        [91.745, 26.14],
                        [91.745, 26.145],
                        [91.74, 26.145],
                        [91.74, 26.14]
                    ]
                ]
            }
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["unit_code"] == "PYTEST-UNIT-001"
    assert data["unit_number"] == "PY-101"
    assert data["area"] == 85.5
    assert data["volume"] == 256.5
    assert data["geometry"]["type"] == "Polygon"