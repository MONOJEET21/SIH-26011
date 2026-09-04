from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_study_area():
    response = client.post(
        "/api/v1/study-areas/",
        json={
            "name": "Pytest Study Area",
            "description": "Created during automated testing",
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [91.70, 26.10],
                        [91.71, 26.10],
                        [91.71, 26.11],
                        [91.70, 26.11],
                        [91.70, 26.10]
                    ]
                ]
            }
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Pytest Study Area"
    assert data["boundary"]["type"] == "Polygon"