from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_negative_underground_asset_depth_rejected():
    payload = {
        "parcel_id": 1,
        "asset_type": "WATER_PIPE",
        "asset_code": "TEST-NEGATIVE-DEPTH-PYTEST",
        "z_min": -5,
        "z_max": -2,
        "depth": -10,
        "status": "ACTIVE",
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [91.8, 26.1],
                [91.81, 26.11]
            ]
        }
    }

    response = client.post("/api/v1/underground-assets/", json=payload)

    assert response.status_code == 400