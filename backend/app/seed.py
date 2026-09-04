import json

from sqlalchemy import func

from app.db.database import SessionLocal
from app.models.study_area import StudyArea
from app.models.parcel import Parcel
from app.models.building import Building
from app.models.floor import Floor
from app.models.property_unit import PropertyUnit
from app.models.underground_asset import UndergroundAsset
from app.models.ulpin import ULPIN


def create_geometry(db, geojson):
    return db.execute(
        func.ST_GeomFromGeoJSON(json.dumps(geojson))
    ).scalar_one()


def seed():
    db = SessionLocal()

    try:
        # -------------------------------------------------
        # 1. STUDY AREA
        # -------------------------------------------------
        study_area = StudyArea(
            name="Demo 3D ULPIN Study Area",
            description="Demo study area for 3D ULPIN property mapping.",
            boundary=create_geometry(
                db,
                {
                    "type": "Polygon",
                    "coordinates": [[
                        [91.80, 26.10],
                        [91.82, 26.10],
                        [91.82, 26.12],
                        [91.80, 26.12],
                        [91.80, 26.10]
                    ]]
                }
            )
        )

        db.add(study_area)
        db.flush()

        # -------------------------------------------------
        # 2. PARCEL
        # -------------------------------------------------
        parcel = Parcel(
            study_area_id=study_area.id,
            parcel_number="DEMO-PARCEL-001",
            parcel_code="DEMO-P001",
            area=1000,
            land_use="RESIDENTIAL",
            status="ACTIVE",
            geometry=create_geometry(
                db,
                {
                    "type": "Polygon",
                    "coordinates": [[
                        [91.801, 26.101],
                        [91.809, 26.101],
                        [91.809, 26.109],
                        [91.801, 26.109],
                        [91.801, 26.101]
                    ]]
                }
            )
        )

        db.add(parcel)
        db.flush()

        # -------------------------------------------------
        # 3. BUILDING
        # -------------------------------------------------
        building = Building(
            parcel_id=parcel.id,
            building_number="DEMO-BUILDING-001",
            building_code="DEMO-B001",
            ground_elevation=10,
            height=12,
            floor_count=2,
            building_type="RESIDENTIAL",
            status="ACTIVE",
            geometry=create_geometry(
                db,
                {
                    "type": "Polygon",
                    "coordinates": [[
                        [91.803, 26.103],
                        [91.807, 26.103],
                        [91.807, 26.107],
                        [91.803, 26.107],
                        [91.803, 26.103]
                    ]]
                }
            )
        )

        db.add(building)
        db.flush()

        # -------------------------------------------------
        # 4. FLOOR 1
        # -------------------------------------------------
        floor_1 = Floor(
            building_id=building.id,
            level_number=1,
            z_min=10,
            z_max=15,
            geometry=create_geometry(
                db,
                {
                    "type": "Polygon",
                    "coordinates": [[
                        [91.803, 26.103],
                        [91.807, 26.103],
                        [91.807, 26.107],
                        [91.803, 26.107],
                        [91.803, 26.103]
                    ]]
                }
            )
        )

        db.add(floor_1)
        db.flush()

        # -------------------------------------------------
        # 5. FLOOR 2
        # -------------------------------------------------
        floor_2 = Floor(
            building_id=building.id,
            level_number=2,
            z_min=15,
            z_max=20,
            geometry=create_geometry(
                db,
                {
                    "type": "Polygon",
                    "coordinates": [[
                        [91.803, 26.103],
                        [91.807, 26.103],
                        [91.807, 26.107],
                        [91.803, 26.107],
                        [91.803, 26.103]
                    ]]
                }
            )
        )

        db.add(floor_2)
        db.flush()

        # -------------------------------------------------
        # 6. PROPERTY UNIT 1
        # -------------------------------------------------
        unit_1 = PropertyUnit(
            floor_id=floor_1.id,
            unit_code="DEMO-U001",
            unit_number="101",
            unit_type="RESIDENTIAL",
            area=500,
            volume=2500,
            ownership_status="OWNED",
            status="ACTIVE",
            geometry=create_geometry(
                db,
                {
                    "type": "Polygon",
                    "coordinates": [[
                        [91.803, 26.103],
                        [91.805, 26.103],
                        [91.805, 26.107],
                        [91.803, 26.107],
                        [91.803, 26.103]
                    ]]
                }
            )
        )

        db.add(unit_1)
        db.flush()

        # -------------------------------------------------
        # 7. PROPERTY UNIT 2
        # -------------------------------------------------
        unit_2 = PropertyUnit(
            floor_id=floor_2.id,
            unit_code="DEMO-U002",
            unit_number="201",
            unit_type="RESIDENTIAL",
            area=500,
            volume=2500,
            ownership_status="OWNED",
            status="ACTIVE",
            geometry=create_geometry(
                db,
                {
                    "type": "Polygon",
                    "coordinates": [[
                        [91.805, 26.103],
                        [91.807, 26.103],
                        [91.807, 26.107],
                        [91.805, 26.107],
                        [91.805, 26.103]
                    ]]
                }
            )
        )

        db.add(unit_2)
        db.flush()

        # -------------------------------------------------
        # 8. UNDERGROUND ASSET
        # -------------------------------------------------
        underground_asset = UndergroundAsset(
            parcel_id=parcel.id,
            asset_type="WATER_PIPE",
            asset_code="DEMO-UA001",
            z_min=-3,
            z_max=-2,
            depth=3,
            status="ACTIVE",
            geometry=create_geometry(
                db,
                {
                    "type": "LineString",
                    "coordinates": [
                        [91.802, 26.102],
                        [91.808, 26.108]
                    ]
                }
            )
        )

        db.add(underground_asset)
        db.flush()

        # -------------------------------------------------
        # 9. ULPIN FOR PROPERTY UNIT 1
        # -------------------------------------------------
        ulpin_1 = ULPIN(
            ulpin="DEMO-ULPIN-000001",
            entity_type="PROPERTY_UNIT",
            entity_id=unit_1.id,
            parent_ulpin=None,
            hierarchy_path=(
                f"STUDY_AREA:{study_area.id}/"
                f"PARCEL:{parcel.id}/"
                f"BUILDING:{building.id}/"
                f"FLOOR:{floor_1.id}/"
                f"PROPERTY_UNIT:{unit_1.id}"
            ),
            status="ACTIVE"
        )

        db.add(ulpin_1)

        # -------------------------------------------------
        # 10. ULPIN FOR PROPERTY UNIT 2
        # -------------------------------------------------
        ulpin_2 = ULPIN(
            ulpin="DEMO-ULPIN-000002",
            entity_type="PROPERTY_UNIT",
            entity_id=unit_2.id,
            parent_ulpin=None,
            hierarchy_path=(
                f"STUDY_AREA:{study_area.id}/"
                f"PARCEL:{parcel.id}/"
                f"BUILDING:{building.id}/"
                f"FLOOR:{floor_2.id}/"
                f"PROPERTY_UNIT:{unit_2.id}"
            ),
            status="ACTIVE"
        )

        db.add(ulpin_2)

        db.commit()

        print("Demo data seeded successfully.")
        print(f"Study Area ID: {study_area.id}")
        print(f"Parcel ID: {parcel.id}")
        print(f"Building ID: {building.id}")
        print(f"Floor 1 ID: {floor_1.id}")
        print(f"Floor 2 ID: {floor_2.id}")
        print(f"Property Unit 1 ID: {unit_1.id}")
        print(f"Property Unit 2 ID: {unit_2.id}")
        print(f"Underground Asset ID: {underground_asset.id}")
        print(f"ULPIN 1: {ulpin_1.ulpin}")
        print(f"ULPIN 2: {ulpin_2.ulpin}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()