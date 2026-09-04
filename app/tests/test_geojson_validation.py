from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_invalid_geojson():
    response = client.post(
        "/api/v1/parcels/",
        json={
            "study_area_id": 1,
            "parcel_number": "INVALID-GEO",
            "parcel_code": "INVALID-GEO-001",
            "area": 100,
            "land_use": "RESIDENTIAL",
            "status": "ACTIVE",
            "geometry": {
                "type": "NotARealGeometry",
                "coordinates": []
            }
        }
    )

    assert response.status_code == 404