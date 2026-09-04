from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_invalid_floor_z_range():
    response = client.post(
        "/api/v1/floors/",
        json={
            "building_id": 1,
            "level_number": 99,
            "z_min": 10,
            "z_max": 5,
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [91.75, 26.16],
                        [91.76, 26.16],
                        [91.76, 26.17],
                        [91.75, 26.17],
                        [91.75, 26.16]
                    ]
                ]
            }
        }
    )

    assert response.status_code == 400