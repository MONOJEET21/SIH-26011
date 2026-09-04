from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_underground_asset():
    response = client.post(
        "/api/v1/underground-assets/",
        json={
            "parcel_id": 1,
            "asset_type": "WATER_PIPE",
            "asset_code": "PYTEST-ASSET-001",
            "z_min": -3,
            "z_max": -2,
            "depth": 3,
            "status": "ACTIVE",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [91.74, 26.14],
                    [91.75, 26.15]
                ]
            }
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["asset_code"] == "PYTEST-ASSET-001"
    assert data["asset_type"] == "WATER_PIPE"
    assert data["z_min"] == -3
    assert data["z_max"] == -2
    assert data["geometry"]["type"] == "LineString"