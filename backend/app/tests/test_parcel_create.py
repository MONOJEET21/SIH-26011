from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_parcel():
    response = client.post(
        "/api/v1/parcels/",
        json={
            "study_area_id": 6,
            "parcel_number": "PYTEST-P-001",
            "parcel_code": "PYTEST-PARCEL-001",
            "area": 100.0,
            "land_use": "RESIDENTIAL",
            "status": "ACTIVE",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [91.72, 26.12],
                        [91.73, 26.12],
                        [91.73, 26.13],
                        [91.72, 26.13],
                        [91.72, 26.12]
                    ]
                ]
            }
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["parcel_number"] == "PYTEST-P-001"
    assert data["parcel_code"] == "PYTEST-PARCEL-001"
    assert data["geometry"]["type"] == "Polygon"