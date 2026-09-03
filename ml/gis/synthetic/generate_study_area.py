from pathlib import Path

import geopandas as gpd
from shapely.geometry import Polygon


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "study_area"
)

CRS = "EPSG:32646"

STUDY_AREA_ID = "AS01"


# ============================================================
# STUDY AREA
# ============================================================

study_area_geometry = Polygon(
    [
        (500000, 2940000),
        (500600, 2940000),
        (500600, 2940600),
        (500000, 2940600),
        (500000, 2940000),
    ]
)

study_area = gpd.GeoDataFrame(
    {
        "study_area_id": [STUDY_AREA_ID],
        "name": ["Synthetic ULPIN Study Area"],
    },
    geometry=[study_area_geometry],
    crs=CRS,
)


# ============================================================
# PARCELS
# ============================================================

parcels = [
    {
        "parcel_id": "P001",
        "study_area_id": STUDY_AREA_ID,
        "parcel_type": "RESIDENTIAL",
        "geometry": Polygon(
            [
                (500030, 2940030),
                (500200, 2940030),
                (500200, 2940270),
                (500030, 2940270),
                (500030, 2940030),
            ]
        ),
    },
    {
        "parcel_id": "P002",
        "study_area_id": STUDY_AREA_ID,
        "parcel_type": "RESIDENTIAL",
        "geometry": Polygon(
            [
                (500220, 2940030),
                (500390, 2940030),
                (500390, 2940270),
                (500220, 2940270),
                (500220, 2940030),
            ]
        ),
    },
    {
        "parcel_id": "P003",
        "study_area_id": STUDY_AREA_ID,
        "parcel_type": "RESIDENTIAL",
        "geometry": Polygon(
            [
                (500410, 2940030),
                (500580, 2940030),
                (500580, 2940270),
                (500410, 2940270),
                (500410, 2940030),
            ]
        ),
    },
]

parcels_gdf = gpd.GeoDataFrame(
    parcels,
    geometry="geometry",
    crs=CRS,
)


# ============================================================
# PARCEL VALIDATION
# ============================================================

if not study_area.geometry.is_valid.all():
    raise ValueError(
        "Study area contains invalid geometry."
    )

if not parcels_gdf.geometry.is_valid.all():
    raise ValueError(
        "One or more parcels contain invalid geometry."
    )


# ------------------------------------------------------------
# Parcel → Study Area containment
# ------------------------------------------------------------

for _, parcel in parcels_gdf.iterrows():

    if not study_area_geometry.contains(
        parcel.geometry
    ):
        raise ValueError(
            f"Parcel {parcel['parcel_id']} "
            f"lies outside the study area."
        )


# ------------------------------------------------------------
# Parcel overlap
# ------------------------------------------------------------

for i in range(len(parcels_gdf)):

    for j in range(i + 1, len(parcels_gdf)):

        parcel_a = parcels_gdf.iloc[i]
        parcel_b = parcels_gdf.iloc[j]

        if parcel_a.geometry.intersects(
            parcel_b.geometry
        ):
            raise ValueError(
                f"Parcel overlap detected: "
                f"{parcel_a['parcel_id']} ↔ "
                f"{parcel_b['parcel_id']}"
            )


# ============================================================
# BUILDINGS
# ============================================================

buildings = [
    {
        "building_id": "B001",
        "parcel_id": "P001",
        "building_type": "RESIDENTIAL",
        "height_m": 15.0,
        "floors_estimated": 5,
        "z_min": 0.0,
        "z_max": 15.0,
        "geometry": Polygon(
            [
                (500060, 2940070),
                (500170, 2940070),
                (500170, 2940230),
                (500060, 2940230),
                (500060, 2940070),
            ]
        ),
    },
    {
        "building_id": "B002",
        "parcel_id": "P002",
        "building_type": "RESIDENTIAL",
        "height_m": 18.0,
        "floors_estimated": 5,
        "z_min": 0.0,
        "z_max": 18.0,
        "geometry": Polygon(
            [
                (500250, 2940070),
                (500360, 2940070),
                (500360, 2940230),
                (500250, 2940230),
                (500250, 2940070),
            ]
        ),
    },
    {
        "building_id": "B003",
        "parcel_id": "P003",
        "building_type": "RESIDENTIAL",
        "height_m": 21.0,
        "floors_estimated": 5,
        "z_min": 0.0,
        "z_max": 21.0,
        "geometry": Polygon(
            [
                (500440, 2940070),
                (500550, 2940070),
                (500550, 2940230),
                (500440, 2940230),
                (500440, 2940070),
            ]
        ),
    },
]

buildings_gdf = gpd.GeoDataFrame(
    buildings,
    geometry="geometry",
    crs=CRS,
)


# ============================================================
# BUILDING VALIDATION
# ============================================================

if not buildings_gdf.geometry.is_valid.all():
    raise ValueError(
        "One or more buildings contain invalid geometry."
    )


# ------------------------------------------------------------
# Building → Parcel containment
# ------------------------------------------------------------

for _, building in buildings_gdf.iterrows():

    parent_parcel = parcels_gdf[
        parcels_gdf["parcel_id"]
        == building["parcel_id"]
    ]

    if len(parent_parcel) != 1:
        raise ValueError(
            f"Parent parcel not found for "
            f"{building['building_id']}"
        )

    parent_geometry = parent_parcel.iloc[0].geometry

    if not parent_geometry.contains(
        building.geometry
    ):
        raise ValueError(
            f"Building {building['building_id']} "
            f"lies outside its parent parcel."
        )


# ------------------------------------------------------------
# Building height validation
# ------------------------------------------------------------

for _, building in buildings_gdf.iterrows():

    calculated_height = (
        building["z_max"]
        - building["z_min"]
    )

    if calculated_height <= 0:
        raise ValueError(
            f"Invalid vertical range for "
            f"{building['building_id']}"
        )

    if abs(
        calculated_height
        - building["height_m"]
    ) > 0.001:

        raise ValueError(
            f"Height mismatch for "
            f"{building['building_id']}"
        )


# ------------------------------------------------------------
# Building overlap validation
# ------------------------------------------------------------

for i in range(len(buildings_gdf)):

    for j in range(i + 1, len(buildings_gdf)):

        building_a = buildings_gdf.iloc[i]
        building_b = buildings_gdf.iloc[j]

        if building_a.geometry.intersects(
            building_b.geometry
        ):
            raise ValueError(
                f"Building overlap detected: "
                f"{building_a['building_id']} ↔ "
                f"{building_b['building_id']}"
            )


# ============================================================
# 🔴 FLOOR GENERATION
# ============================================================

floors = []

for _, building in buildings_gdf.iterrows():

    building_id = building["building_id"]
    parcel_id = building["parcel_id"]

    building_height = float(
        building["height_m"]
    )

    floor_count = int(
        building["floors_estimated"]
    )

    floor_height = (
        building_height / floor_count
    )

    for floor_number in range(
        1,
        floor_count + 1
    ):

        z_min = (
            (floor_number - 1)
            * floor_height
        )

        z_max = (
            floor_number
            * floor_height
        )

        floor_id = (
            f"{building_id}_F"
            f"{floor_number:02d}"
        )

        floors.append(
            {
                "floor_id": floor_id,
                "building_id": building_id,
                "parcel_id": parcel_id,
                "floor_number": floor_number,
                "floor_type": "STANDARD",
                "floor_height_m": floor_height,
                "z_min": z_min,
                "z_max": z_max,
                "geometry": building.geometry,
            }
        )


# ============================================================
# 🔴 BASEMENT
# ============================================================

# One basement is deliberately included in B002.
#
# It extends from -3 m to the ground level (0 m).
#
# This gives us a real underground cadastral volume to
# demonstrate later.

basement_building = buildings_gdf[
    buildings_gdf["building_id"] == "B002"
]

if len(basement_building) != 1:
    raise ValueError(
        "B002 required for synthetic basement."
    )

basement_building = basement_building.iloc[0]

floors.append(
    {
        "floor_id": "B002_B01",
        "building_id": "B002",
        "parcel_id": "P002",
        "floor_number": 0,
        "floor_type": "BASEMENT",
        "floor_height_m": 3.0,
        "z_min": -3.0,
        "z_max": 0.0,
        "geometry": basement_building.geometry,
    }
)


floors_gdf = gpd.GeoDataFrame(
    floors,
    geometry="geometry",
    crs=CRS,
)


# ============================================================
# FLOOR VALIDATION
# ============================================================

if not floors_gdf.geometry.is_valid.all():
    raise ValueError(
        "One or more floor geometries are invalid."
    )


# ------------------------------------------------------------
# Floor → Building containment
# ------------------------------------------------------------

for _, floor in floors_gdf.iterrows():

    parent_building = buildings_gdf[
        buildings_gdf["building_id"]
        == floor["building_id"]
    ]

    if len(parent_building) != 1:
        raise ValueError(
            f"Parent building not found for "
            f"{floor['floor_id']}"
        )

    parent_geometry = (
        parent_building.iloc[0].geometry
    )

    if not parent_geometry.contains(
        floor.geometry
    ):
        raise ValueError(
            f"Floor {floor['floor_id']} "
            f"lies outside its parent building."
        )


# ------------------------------------------------------------
# Floor Z-range validation
# ------------------------------------------------------------

for _, floor in floors_gdf.iterrows():

    if floor["z_max"] <= floor["z_min"]:

        raise ValueError(
            f"Invalid Z range for "
            f"{floor['floor_id']}"
        )


# ------------------------------------------------------------
# Standard floor coverage validation
# ------------------------------------------------------------

for _, building in buildings_gdf.iterrows():

    building_id = building["building_id"]

    building_floors = floors_gdf[
        (floors_gdf["building_id"] == building_id)
        &
        (floors_gdf["floor_type"] == "STANDARD")
    ].sort_values("floor_number")

    expected_floor_count = int(
        building["floors_estimated"]
    )

    if len(building_floors) != expected_floor_count:

        raise ValueError(
            f"Floor count mismatch for "
            f"{building_id}"
        )

    expected_z_min = float(
        building["z_min"]
    )

    expected_z_max = float(
        building["z_max"]
    )

    actual_z_min = float(
        building_floors["z_min"].min()
    )

    actual_z_max = float(
        building_floors["z_max"].max()
    )

    if abs(actual_z_min - expected_z_min) > 0.001:

        raise ValueError(
            f"Floor Z-min coverage mismatch "
            f"for {building_id}"
        )

    if abs(actual_z_max - expected_z_max) > 0.001:

        raise ValueError(
            f"Floor Z-max coverage mismatch "
            f"for {building_id}"
        )


# ============================================================
# WRITE OUTPUTS
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


study_area_path = (
    OUTPUT_DIR / "study_area.geojson"
)

parcels_path = (
    OUTPUT_DIR / "parcels.geojson"
)

buildings_path = (
    OUTPUT_DIR / "buildings.geojson"
)

floors_path = (
    OUTPUT_DIR / "floors.geojson"
)


study_area.to_file(
    study_area_path,
    driver="GeoJSON"
)

parcels_gdf.to_file(
    parcels_path,
    driver="GeoJSON"
)

buildings_gdf.to_file(
    buildings_path,
    driver="GeoJSON"
)

floors_gdf.to_file(
    floors_path,
    driver="GeoJSON"
)


# ============================================================
# SUMMARY
# ============================================================

print("=" * 65)
print("SYNTHETIC 3D CADASTRAL STUDY AREA GENERATED")
print("=" * 65)

print()

print(f"CRS: {CRS}")

print()

print(f"Study area: {study_area_path}")
print(f"Parcels:     {parcels_path}")
print(f"Buildings:   {buildings_path}")
print(f"Floors:      {floors_path}")

print()

print(f"Study area count: {len(study_area)}")
print(f"Parcel count:     {len(parcels_gdf)}")
print(f"Building count:   {len(buildings_gdf)}")

standard_floors = floors_gdf[
    floors_gdf["floor_type"] == "STANDARD"
]

basements = floors_gdf[
    floors_gdf["floor_type"] == "BASEMENT"
]

print(
    f"Standard floor count: {len(standard_floors)}"
)

print(
    f"Basement count:       {len(basements)}"
)

print(
    f"Total vertical levels: {len(floors_gdf)}"
)


print("\nParcel information:")

for _, parcel in parcels_gdf.iterrows():

    print(
        f"  {parcel['parcel_id']} | "
        f"{parcel['parcel_type']} | "
        f"{parcel.geometry.area:,.2f} m²"
    )


print("\nBuilding information:")

for _, building in buildings_gdf.iterrows():

    print(
        f"  {building['building_id']} → "
        f"{building['parcel_id']} | "
        f"{building['floors_estimated']} floors | "
        f"{building['height_m']} m | "
        f"Z: {building['z_min']}–"
        f"{building['z_max']} m"
    )


print("\nFloor information:")

for _, floor in floors_gdf.sort_values(
    ["building_id", "floor_number"]
).iterrows():

    print(
        f"  {floor['floor_id']} | "
        f"{floor['floor_type']} | "
        f"Z: {floor['z_min']:.2f}–"
        f"{floor['z_max']:.2f} m"
    )


print()

print("Study area geometry:        PASSED")
print("Parcel geometry:            PASSED")
print("Parcel containment:         PASSED")
print("Parcel overlap:             PASSED")
print("Building geometry:          PASSED")
print("Building → parcel:          PASSED")
print("Building height validation: PASSED")
print("Building overlap:           PASSED")
print("Floor geometry:             PASSED")
print("Floor → building:           PASSED")
print("Floor Z-range validation:   PASSED")
print("Floor coverage validation:  PASSED")

print()

print("ALL CURRENT VALIDATIONS PASSED")