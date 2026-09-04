from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_negative_parcel_area_rejected():
    payload = {
        "study_area_id": 6,
        "parcel_number": "TEST-NEGATIVE-AREA-PYTEST",
        "parcel_code": "TEST-NEGATIVE-AREA-PYTEST",
        "area": -10,
        "land_use": "RESIDENTIAL",
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

    response = client.post("/api/v1/parcels/", json=payload)

    assert response.status_code == 400