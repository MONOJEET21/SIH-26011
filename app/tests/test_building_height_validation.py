from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_negative_building_height_rejected():
    payload = {
        "parcel_id": 1,
        "building_number": "TEST-NEGATIVE-HEIGHT-PYTEST",
        "building_code": "TEST-NEGATIVE-HEIGHT-PYTEST",
        "ground_elevation": 10,
        "height": -5,
        "floor_count": 2,
        "building_type": "RESIDENTIAL",
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

    response = client.post("/api/v1/buildings/", json=payload)

    assert response.status_code == 400