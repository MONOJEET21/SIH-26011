from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_floor():
    response = client.post(
        "/api/v1/floors/",
        json={
            "building_id": 1,
            "level_number": 10,
            "z_min": 30,
            "z_max": 33,
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

    assert data["level_number"] == 10
    assert data["z_min"] == 30
    assert data["z_max"] == 33
    assert data["geometry"]["type"] == "Polygon"