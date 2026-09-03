from pathlib import Path
import json

import geopandas as gpd
from shapely.geometry import Polygon, box
from shapely.ops import split
from shapely.geometry import LineString


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "study_area"
    / "floors.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "study_area"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "property_units.geojson"
)

CRS = "EPSG:32646"


# ============================================================
# CONFIGURATION
# ============================================================

UNITS_PER_FLOOR = 3


# ============================================================
# LOAD FLOORS
# ============================================================

if not INPUT_FILE.exists():

    raise FileNotFoundError(
        f"Input floor dataset not found:\n{INPUT_FILE}"
    )


floors = gpd.read_file(
    INPUT_FILE
)


# ============================================================
# INPUT VALIDATION
# ============================================================

if floors.empty:

    raise ValueError(
        "Floor dataset is empty."
    )


if floors.crs is None:

    raise ValueError(
        "Floor dataset has no CRS."
    )


if str(floors.crs) != CRS:

    raise ValueError(
        f"Unexpected CRS: {floors.crs}. "
        f"Expected {CRS}."
    )


required_columns = [
    "floor_id",
    "building_id",
    "parcel_id",
    "floor_number",
    "floor_type",
    "z_min",
    "z_max",
]


for column in required_columns:

    if column not in floors.columns:

        raise ValueError(
            f"Missing required column: {column}"
        )


# ============================================================
# REMOVE BASEMENT FROM APARTMENT GENERATION
# ============================================================

standard_floors = floors[
    floors["floor_type"] == "STANDARD"
].copy()


if standard_floors.empty:

    raise ValueError(
        "No standard floors found."
    )


# ============================================================
# HELPER: CREATE UNIT SUBDIVISION
# ============================================================

def create_three_units(
    polygon: Polygon
):
    """
    Divide a building/floor polygon into three
    contiguous property-unit polygons.

    Strategy:

    1. Split the polygon vertically at 40%.
    2. Split the remaining right-hand region
       horizontally at its midpoint.

    Result:

        ┌──────────┬─────────────┐
        │          │             │
        │  UNIT 1  │   UNIT 2    │
        │          │             │
        ├──────────┴─────────────┤
        │         UNIT 3         │
        └────────────────────────┘

    The resulting geometries are clipped by the
    actual source polygon, so units cannot extend
    outside the building footprint.
    """

    min_x, min_y, max_x, max_y = (
        polygon.bounds
    )

    width = max_x - min_x
    height = max_y - min_y

    if width <= 0 or height <= 0:

        raise ValueError(
            "Polygon has invalid dimensions."
        )

    # --------------------------------------------------------
    # First vertical division
    # --------------------------------------------------------

    split_x = (
        min_x
        + width * 0.40
    )

    vertical_line = LineString(
        [
            (split_x, min_y - 1),
            (split_x, max_y + 1),
        ]
    )

    try:

        first_split = split(
            polygon,
            vertical_line
        )

    except Exception as exc:

        raise ValueError(
            f"Unable to vertically split polygon: {exc}"
        )


    parts = list(
        first_split.geoms
    )


    if len(parts) != 2:

        raise ValueError(
            "Vertical split did not create "
            "exactly two regions."
        )


    # --------------------------------------------------------
    # Identify left and right parts
    # --------------------------------------------------------

    parts = sorted(
        parts,
        key=lambda geom: geom.centroid.x
    )


    unit_1 = parts[0]
    right_region = parts[1]


    # --------------------------------------------------------
    # Horizontal division of right region
    # --------------------------------------------------------

    right_min_x, right_min_y, right_max_x, right_max_y = (
        right_region.bounds
    )

    right_mid_y = (
        right_min_y
        + (right_max_y - right_min_y) * 0.50
    )


    horizontal_line = LineString(
        [
            (right_min_x - 1, right_mid_y),
            (right_max_x + 1, right_mid_y),
        ]
    )


    try:

        second_split = split(
            right_region,
            horizontal_line
        )

    except Exception as exc:

        raise ValueError(
            f"Unable to horizontally split polygon: {exc}"
        )


    right_parts = list(
        second_split.geoms
    )


    if len(right_parts) != 2:

        raise ValueError(
            "Horizontal split did not create "
            "exactly two regions."
        )


    right_parts = sorted(
        right_parts,
        key=lambda geom: geom.centroid.y,
        reverse=True,
    )


    unit_2 = right_parts[0]
    unit_3 = right_parts[1]


    units = [
        unit_1,
        unit_2,
        unit_3,
    ]


    # --------------------------------------------------------
    # Clean geometries
    # --------------------------------------------------------

    cleaned_units = []

    for unit in units:

        cleaned = unit.buffer(0)

        if cleaned.is_empty:

            raise ValueError(
                "Generated unit is empty."
            )

        if not cleaned.is_valid:

            raise ValueError(
                "Generated unit is invalid."
            )

        cleaned_units.append(
            cleaned
        )


    return cleaned_units


# ============================================================
# GENERATE UNITS
# ============================================================

unit_records = []


print("=" * 70)
print("SYNTHETIC PROPERTY UNIT GENERATION")
print("=" * 70)

print()

print(
    f"Input floors: {len(standard_floors)}"
)

print(
    f"Units per floor: {UNITS_PER_FLOOR}"
)

print()


# ============================================================
# PROCESS EVERY FLOOR
# ============================================================

for _, floor in standard_floors.iterrows():

    floor_id = floor[
        "floor_id"
    ]

    building_id = floor[
        "building_id"
    ]

    parcel_id = floor[
        "parcel_id"
    ]

    floor_number = int(
        floor["floor_number"]
    )

    z_min = float(
        floor["z_min"]
    )

    z_max = float(
        floor["z_max"]
    )

    floor_polygon = floor.geometry


    # --------------------------------------------------------
    # Geometry validation
    # --------------------------------------------------------

    if not isinstance(
        floor_polygon,
        Polygon
    ):

        raise ValueError(
            f"{floor_id} is not a Polygon."
        )


    if not floor_polygon.is_valid:

        raise ValueError(
            f"{floor_id} has invalid geometry."
        )


    # --------------------------------------------------------
    # Generate three units
    # --------------------------------------------------------

    units = create_three_units(
        floor_polygon
    )


    if len(units) != 3:

        raise ValueError(
            f"{floor_id}: expected 3 units."
        )


    # --------------------------------------------------------
    # Create unit IDs
    # --------------------------------------------------------

    for index, unit_polygon in enumerate(
        units,
        start=1
    ):

        unit_number = (
            floor_number * 100
            + index
        )


        unit_id = (
            f"{building_id}_"
            f"F{floor_number:02d}_"
            f"U{unit_number:04d}"
        )


        # ----------------------------------------------------
        # Unit-level metadata
        # ----------------------------------------------------

        unit_area = (
            unit_polygon.area
        )

        unit_height = (
            z_max - z_min
        )

        unit_volume = (
            unit_area
            * unit_height
        )


        # ----------------------------------------------------
        # Add record
        # ----------------------------------------------------

        unit_records.append(
            {
                "unit_id": unit_id,

                "building_id":
                    building_id,

                "parcel_id":
                    parcel_id,

                "floor_id":
                    floor_id,

                "floor_number":
                    floor_number,

                "unit_number":
                    unit_number,

                "unit_index":
                    index,

                "unit_type":
                    "PROPERTY_UNIT",

                "z_min":
                    z_min,

                "z_max":
                    z_max,

                "height_m":
                    unit_height,

                "area_m2":
                    unit_area,

                "volume_m3":
                    unit_volume,

                "geometry":
                    unit_polygon,
            }
        )


    print(
        f"{floor_id:12} → "
        f"{len(units)} units"
    )


# ============================================================
# CREATE GEODATAFRAME
# ============================================================

units_gdf = gpd.GeoDataFrame(
    unit_records,
    geometry="geometry",
    crs=CRS,
)


# ============================================================
# VALIDATION 1 — UNIT GEOMETRY
# ============================================================

if not units_gdf.geometry.is_valid.all():

    raise ValueError(
        "One or more property-unit geometries "
        "are invalid."
    )


# ============================================================
# VALIDATION 2 — UNIT COUNT
# ============================================================

expected_unit_count = (
    len(standard_floors)
    * UNITS_PER_FLOOR
)


actual_unit_count = len(
    units_gdf
)


if actual_unit_count != expected_unit_count:

    raise ValueError(
        f"Expected {expected_unit_count} units "
        f"but generated {actual_unit_count}."
    )


# ============================================================
# VALIDATION 3 — UNIT AREA COVERAGE
# ============================================================

print()

print(
    "Validating floor coverage..."
)


for floor_id, floor_group in (
    units_gdf.groupby("floor_id")
):

    source_floor = standard_floors[
        standard_floors["floor_id"]
        == floor_id
    ]


    if len(source_floor) != 1:

        raise ValueError(
            f"Could not find source floor "
            f"for {floor_id}."
        )


    source_geometry = (
        source_floor.iloc[0].geometry
    )


    combined_units = (
        floor_group.geometry
        .union_all()
    )


    # --------------------------------------------------------
    # Area equality
    # --------------------------------------------------------

    area_difference = abs(
        combined_units.area
        - source_geometry.area
    )


    if area_difference > 0.01:

        raise ValueError(
            f"{floor_id}: unit area coverage "
            f"differs from floor by "
            f"{area_difference:.6f} m²."
        )


    # --------------------------------------------------------
    # Coverage
    # --------------------------------------------------------

    if not source_geometry.covers(
        combined_units
    ):

        raise ValueError(
            f"{floor_id}: units extend "
            f"outside the floor."
        )


    # --------------------------------------------------------
    # Internal overlap
    # --------------------------------------------------------

    geometries = list(
        floor_group.geometry
    )


    for i in range(
        len(geometries)
    ):

        for j in range(
            i + 1,
            len(geometries)
        ):

            intersection_area = (
                geometries[i]
                .intersection(
                    geometries[j]
                )
                .area
            )


            if intersection_area > 0.01:

                raise ValueError(
                    f"{floor_id}: units "
                    f"overlap."
                )


# ============================================================
# VALIDATION 4 — Z RANGE
# ============================================================

if (
    units_gdf["z_max"]
    <= units_gdf["z_min"]
).any():

    raise ValueError(
        "One or more units have "
        "invalid Z ranges."
    )


# ============================================================
# VALIDATION 5 — UNIT → FLOOR
# ============================================================

print(
    "Validating unit → floor relationships..."
)


for _, unit in units_gdf.iterrows():

    floor = standard_floors[
        standard_floors["floor_id"]
        == unit["floor_id"]
    ]


    if len(floor) != 1:

        raise ValueError(
            f"Missing parent floor for "
            f"{unit['unit_id']}."
        )


    floor_geometry = (
        floor.iloc[0].geometry
    )


    if not floor_geometry.covers(
        unit.geometry
    ):

        raise ValueError(
            f"{unit['unit_id']} lies "
            f"outside its floor."
        )


# ============================================================
# VALIDATION 6 — UNIT → BUILDING
# ============================================================

print(
    "Validating unit → building relationships..."
)


buildings_file = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "study_area"
    / "buildings.geojson"
)


buildings = gpd.read_file(
    buildings_file
)


for _, unit in units_gdf.iterrows():

    building = buildings[
        buildings["building_id"]
        == unit["building_id"]
    ]


    if len(building) != 1:

        raise ValueError(
            f"Missing parent building for "
            f"{unit['unit_id']}."
        )


    building_geometry = (
        building.iloc[0].geometry
    )


    if not building_geometry.covers(
        unit.geometry
    ):

        raise ValueError(
            f"{unit['unit_id']} lies "
            f"outside its building."
        )


# ============================================================
# VALIDATION 7 — UNIT → PARCEL
# ============================================================

print(
    "Validating unit → parcel relationships..."
)


parcels_file = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "study_area"
    / "parcels.geojson"
)


parcels = gpd.read_file(
    parcels_file
)


for _, unit in units_gdf.iterrows():

    parcel = parcels[
        parcels["parcel_id"]
        == unit["parcel_id"]
    ]


    if len(parcel) != 1:

        raise ValueError(
            f"Missing parent parcel for "
            f"{unit['unit_id']}."
        )


    parcel_geometry = (
        parcel.iloc[0].geometry
    )


    if not parcel_geometry.covers(
        unit.geometry
    ):

        raise ValueError(
            f"{unit['unit_id']} lies "
            f"outside its parcel."
        )


# ============================================================
# WRITE OUTPUT
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


units_gdf.to_file(
    OUTPUT_FILE,
    driver="GeoJSON"
)


# ============================================================
# CREATE SUMMARY
# ============================================================

summary = {

    "dataset":
        "Synthetic property units",

    "crs":
        CRS,

    "floor_count":
        len(standard_floors),

    "units_per_floor":
        UNITS_PER_FLOOR,

    "unit_count":
        len(units_gdf),

    "relationships":
        {
            "unit_inside_floor":
                True,

            "unit_inside_building":
                True,

            "unit_inside_parcel":
                True,

            "floor_area_covered":
                True,

            "unit_overlap":
                False,
        },

}


summary_file = (
    OUTPUT_DIR
    / "property_units_summary.json"
)


with open(
    summary_file,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        summary,
        file,
        indent=2,
    )


# ============================================================
# FINAL OUTPUT
# ============================================================

print()

print("=" * 70)
print("PROPERTY UNIT GENERATION COMPLETE")
print("=" * 70)

print()

print(
    f"Standard floors: "
    f"{len(standard_floors)}"
)

print(
    f"Units per floor: "
    f"{UNITS_PER_FLOOR}"
)

print(
    f"Property units: "
    f"{len(units_gdf)}"
)

print()

print(
    f"GeoJSON: "
    f"{OUTPUT_FILE}"
)

print(
    f"Summary: "
    f"{summary_file}"
)

print()

print(
    "Unit geometry validation:       PASSED"
)

print(
    "Unit count validation:          PASSED"
)

print(
    "Floor coverage validation:      PASSED"
)

print(
    "Unit overlap validation:        PASSED"
)

print(
    "Z-range validation:             PASSED"
)

print(
    "Unit → floor validation:        PASSED"
)

print(
    "Unit → building validation:     PASSED"
)

print(
    "Unit → parcel validation:       PASSED"
)

print()

print(
    "ALL PROPERTY UNIT VALIDATIONS PASSED"
)