from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_building():
    response = client.post(
        "/api/v1/buildings/",
        json={
            "parcel_id": 1,
            "building_number": "PYTEST-B-001",
            "building_code": "PYTEST-BUILDING-001",
            "ground_elevation": 0,
            "height": 3,
            "floor_count": 1,
            "building_type": "RESIDENTIAL",
            "status": "ACTIVE",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [91.74, 26.14],
                        [91.75, 26.14],
                        [91.75, 26.15],
                        [91.74, 26.15],
                        [91.74, 26.14]
                    ]
                ]
            }
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["building_number"] == "PYTEST-B-001"
    assert data["building_code"] == "PYTEST-BUILDING-001"
    assert data["geometry"]["type"] == "Polygon"