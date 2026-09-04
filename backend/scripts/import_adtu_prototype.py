import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import text, func

from app.db.database import SessionLocal
from app.models.study_area import StudyArea
from app.models.parcel import Parcel
from app.models.building import Building

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "real"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parcels_data = load_json(DATA_DIR / "adtu_parcels_4326.geojson")
    buildings_data = load_json(DATA_DIR / "adtu_buildings_4326.geojson")
    study_data = load_json(DATA_DIR / "study_area_boundary_4326.geojson")

    db = SessionLocal()
    try:
        db.execute(text("""
            TRUNCATE TABLE
                validation_issues,
                ulpins,
                underground_assets,
                property_units,
                floors,
                buildings,
                parcels,
                study_areas
            RESTART IDENTITY CASCADE
        """))

        now = datetime.utcnow()

        study_area = StudyArea(
            name=study_data["features"][0]["properties"]["name"],
            description=study_data["features"][0]["properties"]["description"],
            boundary=func.ST_GeomFromGeoJSON(
                json.dumps(study_data["features"][0]["geometry"])
            ),
            created_at=now,
            updated_at=now,
        )
        db.add(study_area)
        db.flush()

        parcel_map = {}

        for feature in parcels_data["features"]:
            props = feature["properties"]

            parcel = Parcel(
                study_area_id=study_area.id,
                parcel_number=str(props["parcel_number"]),
                parcel_code=str(props["parcel_code"]),
                area=float(props["area"]),
                land_use=str(props["land_use"]),
                status=str(props["status"]),
                geometry=func.ST_GeomFromGeoJSON(
                    json.dumps(feature["geometry"])
                ),
                created_at=now,
                updated_at=now,
            )

            db.add(parcel)
            db.flush()
            parcel_map[parcel.parcel_code] = parcel.id

        for feature in buildings_data["features"]:
            props = feature["properties"]
            parcel_code = str(props["parcel_code"])

            if parcel_code not in parcel_map:
                raise ValueError(
                    f"Building references unknown parcel_code: {parcel_code}"
                )

            height = props.get("Height_m")
            if height is None:
                height = props.get("height") or 0

            floor_count = props.get("floor_count")
            if floor_count is None:
                levels = props.get("building:levels")
                floor_count = int(float(levels)) if levels else 0

            building = Building(
                parcel_id=parcel_map[parcel_code],
                building_number=str(
                    props.get("Building_ID") or props.get("id")
                ),
                building_code=str(
                    props.get("Building_ID") or props.get("id")
                ),
                ground_elevation=0.0,
                height=float(height),
                floor_count=int(floor_count),
                building_type="INSTITUTIONAL",
                status=str(props.get("status") or "ACTIVE"),
                geometry=func.ST_GeomFromGeoJSON(
                    json.dumps(feature["geometry"])
                ),
                created_at=now,
                updated_at=now,
            )
            db.add(building)

        db.commit()

        print("ADTU prototype import successful.")
        print("Study areas inserted: 1")
        print(f"Parcels inserted: {len(parcels_data['features'])}")
        print(f"Buildings inserted: {len(buildings_data['features'])}")
        print("Floors/property units/underground assets: 0")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
