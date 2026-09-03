"""
3D ULPIN - CADASTRAL TOPOLOGY VALIDATION ENGINE

Purpose
-------
Validate the spatial and hierarchical integrity of the synthetic
3D cadastral study area.

This validator checks:

1. Parcel geometry validity
2. Parcel overlap
3. Building geometry validity
4. Building -> parcel containment
5. Building overlap
6. Building Z-range validity
7. Floor geometry validity
8. Floor -> building containment
9. Floor Z-range validity
10. Floor vertical consistency
11. Property unit geometry validity
12. Property unit -> floor containment
13. Property unit -> building containment
14. Property unit -> parcel containment
15. Property unit Z-range validity
16. Property-unit overlap on the same floor
17. Underground asset geometry validity
18. Underground asset -> parcel containment
19. Underground asset depth validation
20. Underground asset overlap

The output is both human-readable and machine-readable.

IMPORTANT
---------
This is a prototype cadastral validation engine.
It does NOT establish legal ownership or official cadastral validity.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry import Polygon
from shapely.validation import explain_validity


# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

STUDY_AREA_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "study_area"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "outputs"
    / "validation"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_CRS = "EPSG:32646"

PARCELS_FILE = STUDY_AREA_DIR / "parcels.geojson"
BUILDINGS_FILE = STUDY_AREA_DIR / "buildings.geojson"
FLOORS_FILE = STUDY_AREA_DIR / "floors.geojson"
PROPERTY_UNITS_FILE = STUDY_AREA_DIR / "property_units.geojson"
UNDERGROUND_FILE = STUDY_AREA_DIR / "underground_assets.geojson"

REPORT_FILE = OUTPUT_DIR / "topology_validation_report.json"


# ============================================================================
# VALIDATION RESULT STRUCTURE
# ============================================================================

results: list[dict[str, Any]] = []


def record(
    category: str,
    check: str,
    status: str,
    message: str,
    object_id: str | None = None,
    severity: str = "INFO",
) -> None:
    """
    Add one validation result to the report.
    """

    results.append(
        {
            "category": category,
            "check": check,
            "status": status,
            "severity": severity,
            "object_id": object_id,
            "message": message,
        }
    )


def passed(
    category: str,
    check: str,
    message: str,
    object_id: str | None = None,
) -> None:
    record(
        category,
        check,
        "PASSED",
        message,
        object_id,
        "INFO",
    )


def failed(
    category: str,
    check: str,
    message: str,
    object_id: str | None = None,
    severity: str = "HIGH",
) -> None:
    record(
        category,
        check,
        "FAILED",
        message,
        object_id,
        severity,
    )


def warning(
    category: str,
    check: str,
    message: str,
    object_id: str | None = None,
) -> None:
    record(
        category,
        check,
        "WARNING",
        message,
        object_id,
        "MEDIUM",
    )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def load_layer(path: Path, layer_name: str) -> gpd.GeoDataFrame:
    """
    Load a GeoJSON layer and validate its CRS.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"{layer_name} file not found: {path}"
        )

    gdf = gpd.read_file(path)

    if gdf.empty:
        raise ValueError(
            f"{layer_name} contains no features: {path}"
        )

    if gdf.crs is None:
        raise ValueError(
            f"{layer_name} has no CRS."
        )

    if str(gdf.crs) != EXPECTED_CRS:
        raise ValueError(
            f"{layer_name} CRS mismatch. "
            f"Expected {EXPECTED_CRS}, got {gdf.crs}"
        )

    return gdf


def field_value(
    row: Any,
    field: str,
    default: Any = None,
) -> Any:
    """
    Safely retrieve an attribute.
    """

    try:
        value = row[field]

        if value is None:
            return default

        return value

    except (KeyError, TypeError):
        return default


def get_id(
    row: Any,
    candidates: list[str],
    fallback: str,
) -> str:
    """
    Find the first available identifier field.
    """

    for field in candidates:
        value = field_value(row, field)

        if value is not None:
            return str(value)

    return fallback


def z_value(
    row: Any,
    field: str,
) -> float | None:
    """
    Convert a Z attribute to float.
    """

    value = field_value(row, field)

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def geometries_overlap(
    geom_a,
    geom_b,
    tolerance: float = 0.01,
) -> bool:
    """
    Determine whether two polygons have a meaningful area overlap.

    Merely touching along a boundary is NOT considered an overlap.
    """

    if geom_a is None or geom_b is None:
        return False

    if geom_a.is_empty or geom_b.is_empty:
        return False

    intersection = geom_a.intersection(geom_b)

    if intersection.is_empty:
        return False

    return intersection.area > tolerance


def geometry_inside(
    child,
    parent,
    tolerance: float = 0.01,
) -> bool:
    """
    Check whether child geometry is inside or covered by parent geometry.

    covers() is intentionally used instead of contains() so that a
    child touching the parent's boundary is not automatically rejected.
    """

    if child is None or parent is None:
        return False

    if child.is_empty or parent.is_empty:
        return False

    return parent.buffer(tolerance).covers(child)


# ============================================================================
# LOAD DATA
# ============================================================================

print("=" * 78)
print("3D CADASTRAL TOPOLOGY VALIDATION ENGINE")
print("=" * 78)
print()

print(f"Expected CRS: {EXPECTED_CRS}")
print(f"Study area directory: {STUDY_AREA_DIR}")
print()

parcels = load_layer(
    PARCELS_FILE,
    "Parcels",
)

buildings = load_layer(
    BUILDINGS_FILE,
    "Buildings",
)

floors = load_layer(
    FLOORS_FILE,
    "Floors",
)

property_units = load_layer(
    PROPERTY_UNITS_FILE,
    "Property units",
)

underground_assets = load_layer(
    UNDERGROUND_FILE,
    "Underground assets",
)


print(f"Parcels:             {len(parcels)}")
print(f"Buildings:           {len(buildings)}")
print(f"Floors:              {len(floors)}")
print(f"Property units:      {len(property_units)}")
print(f"Underground assets:  {len(underground_assets)}")
print()


# ============================================================================
# BUILD LOOKUP TABLES
# ============================================================================

parcel_lookup: dict[str, Any] = {}

for index, row in parcels.iterrows():

    parcel_id = get_id(
        row,
        ["parcel_id", "id"],
        f"PARCEL_{index}",
    )

    parcel_lookup[parcel_id] = row.geometry


building_lookup: dict[str, Any] = {}

for index, row in buildings.iterrows():

    building_id = get_id(
        row,
        ["building_id", "id"],
        f"BUILDING_{index}",
    )

    building_lookup[building_id] = row.geometry


floor_lookup: dict[str, Any] = {}

for index, row in floors.iterrows():

    floor_id = get_id(
        row,
        ["floor_id", "id"],
        f"FLOOR_{index}",
    )

    floor_lookup[floor_id] = row.geometry


unit_lookup: dict[str, Any] = {}

for index, row in property_units.iterrows():

    unit_id = get_id(
        row,
        ["unit_id", "property_unit_id", "id"],
        f"UNIT_{index}",
    )

    unit_lookup[unit_id] = row.geometry


# ============================================================================
# 1. PARCEL GEOMETRY VALIDATION
# ============================================================================

print("=" * 78)
print("PARCEL VALIDATION")
print("=" * 78)

parcel_geometry_failed = False

for index, row in parcels.iterrows():

    parcel_id = get_id(
        row,
        ["parcel_id", "id"],
        f"PARCEL_{index}",
    )

    geometry = row.geometry

    if geometry is None or geometry.is_empty:

        failed(
            "PARCEL",
            "geometry_validity",
            "Parcel has empty or missing geometry.",
            parcel_id,
        )

        parcel_geometry_failed = True
        continue

    if not geometry.is_valid:

        failed(
            "PARCEL",
            "geometry_validity",
            f"Invalid geometry: {explain_validity(geometry)}",
            parcel_id,
        )

        parcel_geometry_failed = True

if not parcel_geometry_failed:

    passed(
        "PARCEL",
        "geometry_validity",
        "All parcel geometries are valid.",
    )


# ============================================================================
# 2. PARCEL OVERLAP
# ============================================================================

parcel_overlap_failed = False

parcel_rows = list(parcels.iterrows())

for i in range(len(parcel_rows)):

    index_a, row_a = parcel_rows[i]

    id_a = get_id(
        row_a,
        ["parcel_id", "id"],
        f"PARCEL_{index_a}",
    )

    for j in range(i + 1, len(parcel_rows)):

        index_b, row_b = parcel_rows[j]

        id_b = get_id(
            row_b,
            ["parcel_id", "id"],
            f"PARCEL_{index_b}",
        )

        if geometries_overlap(
            row_a.geometry,
            row_b.geometry,
        ):

            failed(
                "PARCEL",
                "overlap",
                f"Parcel {id_a} overlaps parcel {id_b}.",
                f"{id_a}|{id_b}",
            )

            parcel_overlap_failed = True


if not parcel_overlap_failed:

    passed(
        "PARCEL",
        "overlap",
        "No meaningful parcel overlaps detected.",
    )


# ============================================================================
# 3. BUILDING GEOMETRY + PARENT VALIDATION
# ============================================================================

print()
print("=" * 78)
print("BUILDING VALIDATION")
print("=" * 78)

building_geometry_failed = False
building_parent_failed = False
building_z_failed = False

for index, row in buildings.iterrows():

    building_id = get_id(
        row,
        ["building_id", "id"],
        f"BUILDING_{index}",
    )

    parcel_id = get_id(
        row,
        ["parcel_id", "parent_parcel_id"],
        "",
    )

    geometry = row.geometry

    # Geometry

    if geometry is None or geometry.is_empty:

        failed(
            "BUILDING",
            "geometry_validity",
            "Building has empty or missing geometry.",
            building_id,
        )

        building_geometry_failed = True

    elif not geometry.is_valid:

        failed(
            "BUILDING",
            "geometry_validity",
            f"Invalid geometry: {explain_validity(geometry)}",
            building_id,
        )

        building_geometry_failed = True

    # Parent parcel

    if parcel_id not in parcel_lookup:

        failed(
            "BUILDING",
            "parent_reference",
            f"Parent parcel {parcel_id} does not exist.",
            building_id,
        )

        building_parent_failed = True

    elif not geometry_inside(
        geometry,
        parcel_lookup[parcel_id],
    ):

        failed(
            "BUILDING",
            "parcel_containment",
            f"Building is outside parent parcel {parcel_id}.",
            building_id,
        )

        building_parent_failed = True

    # Z range

    z_min = z_value(row, "z_min")
    z_max = z_value(row, "z_max")

    if z_min is None or z_max is None:

        failed(
            "BUILDING",
            "z_range",
            "Building is missing z_min or z_max.",
            building_id,
        )

        building_z_failed = True

    elif z_max <= z_min:

        failed(
            "BUILDING",
            "z_range",
            f"Invalid Z range: {z_min}–{z_max}.",
            building_id,
        )

        building_z_failed = True


if not building_geometry_failed:

    passed(
        "BUILDING",
        "geometry_validity",
        "All building geometries are valid.",
    )

if not building_parent_failed:

    passed(
        "BUILDING",
        "parcel_containment",
        "All buildings are contained within their parent parcels.",
    )

if not building_z_failed:

    passed(
        "BUILDING",
        "z_range",
        "All building Z ranges are valid.",
    )


# ============================================================================
# 4. BUILDING OVERLAP
# ============================================================================

building_overlap_failed = False

building_rows = list(buildings.iterrows())

for i in range(len(building_rows)):

    index_a, row_a = building_rows[i]

    id_a = get_id(
        row_a,
        ["building_id", "id"],
        f"BUILDING_{index_a}",
    )

    for j in range(i + 1, len(building_rows)):

        index_b, row_b = building_rows[j]

        id_b = get_id(
            row_b,
            ["building_id", "id"],
            f"BUILDING_{index_b}",
        )

        if geometries_overlap(
            row_a.geometry,
            row_b.geometry,
        ):

            failed(
                "BUILDING",
                "overlap",
                f"Building {id_a} overlaps building {id_b}.",
                f"{id_a}|{id_b}",
            )

            building_overlap_failed = True


if not building_overlap_failed:

    passed(
        "BUILDING",
        "overlap",
        "No meaningful building overlaps detected.",
    )


# ============================================================================
# 5. FLOOR VALIDATION
# ============================================================================

print()
print("=" * 78)
print("FLOOR VALIDATION")
print("=" * 78)

floor_geometry_failed = False
floor_parent_failed = False
floor_z_failed = False

for index, row in floors.iterrows():

    floor_id = get_id(
        row,
        ["floor_id", "id"],
        f"FLOOR_{index}",
    )

    building_id = get_id(
        row,
        ["building_id", "parent_building_id"],
        "",
    )

    geometry = row.geometry

    # Geometry

    if geometry is None or geometry.is_empty:

        failed(
            "FLOOR",
            "geometry_validity",
            "Floor has empty or missing geometry.",
            floor_id,
        )

        floor_geometry_failed = True

    elif not geometry.is_valid:

        failed(
            "FLOOR",
            "geometry_validity",
            f"Invalid geometry: {explain_validity(geometry)}",
            floor_id,
        )

        floor_geometry_failed = True

    # Parent building

    if building_id not in building_lookup:

        failed(
            "FLOOR",
            "parent_reference",
            f"Parent building {building_id} does not exist.",
            floor_id,
        )

        floor_parent_failed = True

    elif not geometry_inside(
        geometry,
        building_lookup[building_id],
    ):

        failed(
            "FLOOR",
            "building_containment",
            f"Floor is outside parent building {building_id}.",
            floor_id,
        )

        floor_parent_failed = True

    # Z

    z_min = z_value(row, "z_min")
    z_max = z_value(row, "z_max")

    if z_min is None or z_max is None:

        failed(
            "FLOOR",
            "z_range",
            "Floor is missing z_min or z_max.",
            floor_id,
        )

        floor_z_failed = True

    elif z_max <= z_min:

        failed(
            "FLOOR",
            "z_range",
            f"Invalid floor Z range: {z_min}–{z_max}.",
            floor_id,
        )

        floor_z_failed = True


if not floor_geometry_failed:

    passed(
        "FLOOR",
        "geometry_validity",
        "All floor geometries are valid.",
    )

if not floor_parent_failed:

    passed(
        "FLOOR",
        "building_containment",
        "All floors are contained within their parent buildings.",
    )

if not floor_z_failed:

    passed(
        "FLOOR",
        "z_range",
        "All floor Z ranges are valid.",
    )


# ============================================================================
# 6. FLOOR VERTICAL CONSISTENCY
# ============================================================================

floor_vertical_failed = False

floors_by_building: dict[str, list[dict[str, Any]]] = {}

for index, row in floors.iterrows():

    floor_id = get_id(
        row,
        ["floor_id", "id"],
        f"FLOOR_{index}",
    )

    building_id = get_id(
        row,
        ["building_id", "parent_building_id"],
        "",
    )

    z_min = z_value(row, "z_min")
    z_max = z_value(row, "z_max")

    if z_min is None or z_max is None:
        continue

    floors_by_building.setdefault(
        building_id,
        [],
    ).append(
        {
            "floor_id": floor_id,
            "z_min": z_min,
            "z_max": z_max,
        }
    )


for building_id, building_floors in floors_by_building.items():

    building_floors.sort(
        key=lambda item: item["z_min"]
    )

    for i in range(len(building_floors) - 1):

        current = building_floors[i]
        next_floor = building_floors[i + 1]

        current_top = current["z_max"]
        next_bottom = next_floor["z_min"]

        tolerance = 0.001

        if next_bottom < current_top - tolerance:

            failed(
                "FLOOR",
                "vertical_consistency",
                (
                    f"Vertical overlap between "
                    f"{current['floor_id']} and "
                    f"{next_floor['floor_id']}."
                ),
                building_id,
            )

            floor_vertical_failed = True

        elif next_bottom > current_top + tolerance:

            warning(
                "FLOOR",
                "vertical_consistency",
                (
                    f"Vertical gap detected between "
                    f"{current['floor_id']} and "
                    f"{next_floor['floor_id']}."
                ),
                building_id,
            )


if not floor_vertical_failed:

    passed(
        "FLOOR",
        "vertical_consistency",
        "No invalid vertical floor overlaps detected.",
    )


# ============================================================================
# 7. PROPERTY UNIT VALIDATION
# ============================================================================

print()
print("=" * 78)
print("PROPERTY UNIT VALIDATION")
print("=" * 78)

unit_geometry_failed = False
unit_floor_failed = False
unit_building_failed = False
unit_parcel_failed = False
unit_z_failed = False

units_by_floor: dict[str, list[tuple[int, Any]]] = {}

for index, row in property_units.iterrows():

    unit_id = get_id(
        row,
        ["unit_id", "property_unit_id", "id"],
        f"UNIT_{index}",
    )

    floor_id = get_id(
        row,
        ["floor_id", "parent_floor_id"],
        "",
    )

    building_id = get_id(
        row,
        ["building_id", "parent_building_id"],
        "",
    )

    parcel_id = get_id(
        row,
        ["parcel_id", "parent_parcel_id"],
        "",
    )

    geometry = row.geometry

    # Geometry

    if geometry is None or geometry.is_empty:

        failed(
            "PROPERTY_UNIT",
            "geometry_validity",
            "Property unit has empty or missing geometry.",
            unit_id,
        )

        unit_geometry_failed = True

    elif not geometry.is_valid:

        failed(
            "PROPERTY_UNIT",
            "geometry_validity",
            f"Invalid geometry: {explain_validity(geometry)}",
            unit_id,
        )

        unit_geometry_failed = True

    # Floor

    if floor_id not in floor_lookup:

        failed(
            "PROPERTY_UNIT",
            "floor_reference",
            f"Parent floor {floor_id} does not exist.",
            unit_id,
        )

        unit_floor_failed = True

    elif not geometry_inside(
        geometry,
        floor_lookup[floor_id],
    ):

        failed(
            "PROPERTY_UNIT",
            "floor_containment",
            f"Unit is outside parent floor {floor_id}.",
            unit_id,
        )

        unit_floor_failed = True

    # Building

    if building_id not in building_lookup:

        failed(
            "PROPERTY_UNIT",
            "building_reference",
            f"Parent building {building_id} does not exist.",
            unit_id,
        )

        unit_building_failed = True

    elif not geometry_inside(
        geometry,
        building_lookup[building_id],
    ):

        failed(
            "PROPERTY_UNIT",
            "building_containment",
            f"Unit is outside parent building {building_id}.",
            unit_id,
        )

        unit_building_failed = True

    # Parcel

    if parcel_id not in parcel_lookup:

        failed(
            "PROPERTY_UNIT",
            "parcel_reference",
            f"Parent parcel {parcel_id} does not exist.",
            unit_id,
        )

        unit_parcel_failed = True

    elif not geometry_inside(
        geometry,
        parcel_lookup[parcel_id],
    ):

        failed(
            "PROPERTY_UNIT",
            "parcel_containment",
            f"Unit is outside parent parcel {parcel_id}.",
            unit_id,
        )

        unit_parcel_failed = True

    # Z range

    z_min = z_value(row, "z_min")
    z_max = z_value(row, "z_max")

    if z_min is None or z_max is None:

        failed(
            "PROPERTY_UNIT",
            "z_range",
            "Property unit is missing z_min or z_max.",
            unit_id,
        )

        unit_z_failed = True

    elif z_max <= z_min:

        failed(
            "PROPERTY_UNIT",
            "z_range",
            f"Invalid unit Z range: {z_min}–{z_max}.",
            unit_id,
        )

        unit_z_failed = True

    # Save for floor overlap validation

    units_by_floor.setdefault(
        floor_id,
        []
    ).append(
        (index, row)
    )


if not unit_geometry_failed:

    passed(
        "PROPERTY_UNIT",
        "geometry_validity",
        "All property-unit geometries are valid.",
    )

if not unit_floor_failed:

    passed(
        "PROPERTY_UNIT",
        "floor_containment",
        "All property units are contained within their parent floors.",
    )

if not unit_building_failed:

    passed(
        "PROPERTY_UNIT",
        "building_containment",
        "All property units are contained within their parent buildings.",
    )

if not unit_parcel_failed:

    passed(
        "PROPERTY_UNIT",
        "parcel_containment",
        "All property units are contained within their parent parcels.",
    )

if not unit_z_failed:

    passed(
        "PROPERTY_UNIT",
        "z_range",
        "All property-unit Z ranges are valid.",
    )


# ============================================================================
# 8. PROPERTY UNIT OVERLAP
# ============================================================================

unit_overlap_failed = False

for floor_id, unit_rows in units_by_floor.items():

    for i in range(len(unit_rows)):

        index_a, row_a = unit_rows[i]

        id_a = get_id(
            row_a,
            ["unit_id", "property_unit_id", "id"],
            f"UNIT_{index_a}",
        )

        for j in range(i + 1, len(unit_rows)):

            index_b, row_b = unit_rows[j]

            id_b = get_id(
                row_b,
                ["unit_id", "property_unit_id", "id"],
                f"UNIT_{index_b}",
            )

            if geometries_overlap(
                row_a.geometry,
                row_b.geometry,
            ):

                failed(
                    "PROPERTY_UNIT",
                    "overlap",
                    (
                        f"Property unit {id_a} overlaps "
                        f"property unit {id_b} on floor {floor_id}."
                    ),
                    f"{id_a}|{id_b}",
                )

                unit_overlap_failed = True


if not unit_overlap_failed:

    passed(
        "PROPERTY_UNIT",
        "overlap",
        "No meaningful property-unit overlaps detected.",
    )


# ============================================================================
# 9. UNIT Z RANGE VS FLOOR Z RANGE
# ============================================================================

unit_floor_z_failed = False

for index, row in property_units.iterrows():

    unit_id = get_id(
        row,
        ["unit_id", "property_unit_id", "id"],
        f"UNIT_{index}",
    )

    floor_id = get_id(
        row,
        ["floor_id", "parent_floor_id"],
        "",
    )

    unit_z_min = z_value(row, "z_min")
    unit_z_max = z_value(row, "z_max")

    if floor_id not in floor_lookup:
        continue

    floor_rows = floors[
        floors.apply(
            lambda r: get_id(
                r,
                ["floor_id", "id"],
                "",
            )
            == floor_id,
            axis=1,
        )
    ]

    if floor_rows.empty:
        continue

    floor_row = floor_rows.iloc[0]

    floor_z_min = z_value(
        floor_row,
        "z_min",
    )

    floor_z_max = z_value(
        floor_row,
        "z_max",
    )

    if (
        unit_z_min is None
        or unit_z_max is None
        or floor_z_min is None
        or floor_z_max is None
    ):
        continue

    tolerance = 0.001

    if (
        unit_z_min < floor_z_min - tolerance
        or unit_z_max > floor_z_max + tolerance
    ):

        failed(
            "PROPERTY_UNIT",
            "floor_z_containment",
            (
                f"Unit Z range {unit_z_min}–{unit_z_max} "
                f"exceeds floor {floor_id} range "
                f"{floor_z_min}–{floor_z_max}."
            ),
            unit_id,
        )

        unit_floor_z_failed = True


if not unit_floor_z_failed:

    passed(
        "PROPERTY_UNIT",
        "floor_z_containment",
        "All property-unit Z ranges fit within their parent floors.",
    )


# ============================================================================
# 10. UNDERGROUND ASSET VALIDATION
# ============================================================================

print()
print("=" * 78)
print("UNDERGROUND ASSET VALIDATION")
print("=" * 78)

asset_geometry_failed = False
asset_parent_failed = False
asset_depth_failed = False

for index, row in underground_assets.iterrows():

    asset_id = get_id(
        row,
        ["asset_id", "underground_asset_id", "id"],
        f"ASSET_{index}",
    )

    parcel_id = get_id(
        row,
        ["parcel_id", "parent_parcel_id"],
        "",
    )

    geometry = row.geometry

    # Geometry

    if geometry is None or geometry.is_empty:

        failed(
            "UNDERGROUND_ASSET",
            "geometry_validity",
            "Underground asset has empty or missing geometry.",
            asset_id,
        )

        asset_geometry_failed = True

    elif not geometry.is_valid:

        failed(
            "UNDERGROUND_ASSET",
            "geometry_validity",
            f"Invalid geometry: {explain_validity(geometry)}",
            asset_id,
        )

        asset_geometry_failed = True

    # Parcel containment

    if parcel_id not in parcel_lookup:

        failed(
            "UNDERGROUND_ASSET",
            "parcel_reference",
            f"Parent parcel {parcel_id} does not exist.",
            asset_id,
        )

        asset_parent_failed = True

    elif not geometry_inside(
        geometry,
        parcel_lookup[parcel_id],
    ):

        failed(
            "UNDERGROUND_ASSET",
            "parcel_containment",
            (
                f"Underground asset is outside "
                f"parent parcel {parcel_id}."
            ),
            asset_id,
        )

        asset_parent_failed = True

    # Depth / Z range

    z_min = z_value(row, "z_min")
    z_max = z_value(row, "z_max")

    if z_min is None or z_max is None:

        failed(
            "UNDERGROUND_ASSET",
            "depth_range",
            "Underground asset is missing z_min or z_max.",
            asset_id,
        )

        asset_depth_failed = True

    elif z_max <= z_min:

        failed(
            "UNDERGROUND_ASSET",
            "depth_range",
            f"Invalid underground Z range: {z_min}–{z_max}.",
            asset_id,
        )

        asset_depth_failed = True

    elif z_max > 0:

        warning(
            "UNDERGROUND_ASSET",
            "depth_range",
            (
                f"Asset has a portion above Z=0: "
                f"{z_min}–{z_max}."
            ),
            asset_id,
        )


if not asset_geometry_failed:

    passed(
        "UNDERGROUND_ASSET",
        "geometry_validity",
        "All underground asset geometries are valid.",
    )

if not asset_parent_failed:

    passed(
        "UNDERGROUND_ASSET",
        "parcel_containment",
        "All underground assets are contained within their parent parcels.",
    )

if not asset_depth_failed:

    passed(
        "UNDERGROUND_ASSET",
        "depth_range",
        "All underground asset depth ranges are valid.",
    )


# ============================================================================
# 11. UNDERGROUND ASSET OVERLAP
# ============================================================================

asset_overlap_failed = False

asset_rows = list(underground_assets.iterrows())

for i in range(len(asset_rows)):

    index_a, row_a = asset_rows[i]

    id_a = get_id(
        row_a,
        ["asset_id", "underground_asset_id", "id"],
        f"ASSET_{index_a}",
    )

    for j in range(i + 1, len(asset_rows)):

        index_b, row_b = asset_rows[j]

        id_b = get_id(
            row_b,
            ["asset_id", "underground_asset_id", "id"],
            f"ASSET_{index_b}",
        )

        if geometries_overlap(
            row_a.geometry,
            row_b.geometry,
        ):

            failed(
                "UNDERGROUND_ASSET",
                "overlap",
                (
                    f"Underground asset {id_a} "
                    f"overlaps underground asset {id_b}."
                ),
                f"{id_a}|{id_b}",
            )

            asset_overlap_failed = True


if not asset_overlap_failed:

    passed(
        "UNDERGROUND_ASSET",
        "overlap",
        "No meaningful underground asset overlaps detected.",
    )


# ============================================================================
# OVERALL RESULT
# ============================================================================

failed_results = [
    result
    for result in results
    if result["status"] == "FAILED"
]

warning_results = [
    result
    for result in results
    if result["status"] == "WARNING"
]


overall_status = (
    "FAILED"
    if failed_results
    else "PASSED"
)


# ============================================================================
# BUILD SUMMARY
# ============================================================================

summary = {
    "project": "3D ULPIN Prototype",
    "validator": "Cadastral Topology Validation Engine",
    "version": "1.0.0",
    "crs": EXPECTED_CRS,
    "overall_status": overall_status,
    "statistics": {
        "parcels": len(parcels),
        "buildings": len(buildings),
        "floors": len(floors),
        "property_units": len(property_units),
        "underground_assets": len(underground_assets),
        "total_checks": len(results),
        "failed_checks": len(failed_results),
        "warnings": len(warning_results),
    },
    "results": results,
}


# ============================================================================
# WRITE REPORT
# ============================================================================

with REPORT_FILE.open(
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        summary,
        file,
        indent=2,
        ensure_ascii=False,
    )


# ============================================================================
# FINAL CONSOLE OUTPUT
# ============================================================================

print()
print("=" * 78)
print("TOPOLOGY VALIDATION COMPLETE")
print("=" * 78)
print()

print(f"Overall status:      {overall_status}")
print(f"Total checks:        {len(results)}")
print(f"Failed checks:       {len(failed_results)}")
print(f"Warnings:            {len(warning_results)}")
print()

print("Validation report:")
print(REPORT_FILE)
print()


if failed_results:

    print("=" * 78)
    print("FAILED VALIDATIONS")
    print("=" * 78)

    for result in failed_results:

        object_text = (
            f" [{result['object_id']}]"
            if result["object_id"]
            else ""
        )

        print(
            f"FAIL | "
            f"{result['category']} | "
            f"{result['check']}"
            f"{object_text}"
        )

        print(
            f"      {result['message']}"
        )

        print()

else:

    print("=" * 78)
    print("ALL CADASTRAL TOPOLOGY VALIDATIONS PASSED")
    print("=" * 78)

    print()
    print("Spatial hierarchy is internally consistent.")
    print("The dataset is ready for the next pipeline stage.")