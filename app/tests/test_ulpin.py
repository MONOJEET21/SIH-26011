from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_ulpin():
    response = client.get(
        "/api/v1/ulpins/ULPIN-ASSAM-000002"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["ulpin"]["ulpin"] == "ULPIN-ASSAM-000002"
    assert data["property_unit"] is not None
    assert data["floor"] is not None
    assert data["building"] is not None
    assert data["parcel"] is not None
    assert data["study_area"] is not None