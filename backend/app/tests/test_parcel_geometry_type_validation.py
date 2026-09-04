from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_parcel_point_geometry_rejected():
    payload = {
        "study_area_id": 6,
        "parcel_number": "TEST-POINT-GEOMETRY",
        "parcel_code": "TEST-POINT-GEOMETRY",
        "area": 100,
        "land_use": "RESIDENTIAL",
        "status": "ACTIVE",
        "geometry": {
            "type": "Point",
            "coordinates": [91.8, 26.1]
        }
    }

    response = client.post("/api/v1/parcels/", json=payload)

    assert response.status_code == 400