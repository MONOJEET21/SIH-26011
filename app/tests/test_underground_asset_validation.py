from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_invalid_underground_asset_z_range():
    response = client.post(
        "/api/v1/underground-assets/",
        json={
            "parcel_id": 1,
            "asset_type": "WATER_PIPE",
            "asset_code": "TEST-INVALID-Z",
            "z_min": 5,
            "z_max": 2,
            "depth": 3,
            "status": "ACTIVE",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [91.75, 26.16],
                    [91.76, 26.17]
                ]
            }
        }
    )

    assert response.status_code == 400