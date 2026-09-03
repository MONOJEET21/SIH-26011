from pathlib import Path
import json

import geopandas as gpd
import trimesh
from shapely.affinity import translate


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "study_area"
    / "property_units.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "outputs"
    / "3d"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "property_units_3d.obj"
)

METADATA_FILE = (
    OUTPUT_DIR
    / "property_units_3d_metadata.json"
)

CRS = "EPSG:32646"


# ============================================================
# LOCAL COORDINATE ORIGIN
# ============================================================

ORIGIN_X = 500000.0
ORIGIN_Y = 2940000.0


# ============================================================
# VALIDATION TOLERANCES
# ============================================================

AREA_TOLERANCE_M2 = 0.01
VOLUME_TOLERANCE_M3 = 0.01


# ============================================================
# LOAD PROPERTY UNITS
# ============================================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Property unit dataset not found:\n{INPUT_FILE}"
    )

units = gpd.read_file(INPUT_FILE)


# ============================================================
# INPUT VALIDATION
# ============================================================

if units.empty:
    raise ValueError(
        "Property unit dataset is empty."
    )

if units.crs is None:
    raise ValueError(
        "Property unit dataset has no CRS."
    )

if str(units.crs) != CRS:
    raise ValueError(
        f"Unexpected CRS: {units.crs}. "
        f"Expected {CRS}."
    )


required_columns = [
    "unit_id",
    "building_id",
    "parcel_id",
    "floor_id",
    "floor_number",
    "unit_number",
    "unit_type",
    "z_min",
    "z_max",
    "area_m2",
    "volume_m3",
]

for column in required_columns:
    if column not in units.columns:
        raise ValueError(
            f"Required column missing: {column}"
        )


if not units.geometry.is_valid.all():
    raise ValueError(
        "One or more property-unit geometries are invalid."
    )


# ============================================================
# UNIT COUNT
# ============================================================

EXPECTED_UNIT_COUNT = 45

if len(units) != EXPECTED_UNIT_COUNT:
    raise ValueError(
        f"Expected {EXPECTED_UNIT_COUNT} "
        f"property units but found {len(units)}."
    )


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# EXTRUDE ONE PROPERTY UNIT
# ============================================================

def extrude_property_unit(
    polygon,
    z_min,
    z_max,
):
    """
    Convert a 2D property-unit polygon into
    a watertight 3D solid.

    The polygon is translated into a local XY
    coordinate system and extruded vertically.
    """

    # --------------------------------------------------------
    # Validate Z
    # --------------------------------------------------------

    if z_max <= z_min:
        raise ValueError(
            f"Invalid Z range: "
            f"{z_min} → {z_max}"
        )

    height = z_max - z_min


    # --------------------------------------------------------
    # Translate polygon to local coordinates
    # --------------------------------------------------------

    local_polygon = translate(
        polygon,
        xoff=-ORIGIN_X,
        yoff=-ORIGIN_Y,
    )


    # --------------------------------------------------------
    # Create 3D solid
    # --------------------------------------------------------

    try:
        mesh = trimesh.creation.extrude_polygon(
            local_polygon,
            height=height,
        )

    except Exception as exc:
        raise RuntimeError(
            f"3D polygon extrusion failed: {exc}"
        )


    # --------------------------------------------------------
    # Move solid to actual Z position
    # --------------------------------------------------------

    mesh.apply_translation(
        [0.0, 0.0, z_min]
    )


    # --------------------------------------------------------
    # Clean mesh
    # --------------------------------------------------------

    mesh.merge_vertices()

    mesh.process(
        validate=True
    )


    return mesh


# ============================================================
# START PROCESSING
# ============================================================

unit_metadata = []
unit_meshes = []


print("=" * 70)
print("3D PROPERTY UNIT VOLUME RECONSTRUCTION")
print("=" * 70)

print()

print(
    f"Input: {INPUT_FILE}"
)

print(
    f"CRS: {CRS}"
)

print(
    f"Local origin: "
    f"({ORIGIN_X}, {ORIGIN_Y})"
)

print()

print(
    f"Property units to process: {len(units)}"
)

print()


# ============================================================
# SORT UNITS
# ============================================================

units = units.sort_values(
    [
        "building_id",
        "floor_number",
        "unit_number",
    ]
)


# ============================================================
# PROCESS EVERY PROPERTY UNIT
# ============================================================

for _, unit in units.iterrows():

    unit_id = unit["unit_id"]
    building_id = unit["building_id"]
    floor_id = unit["floor_id"]
    parcel_id = unit["parcel_id"]

    floor_number = int(
        unit["floor_number"]
    )

    unit_number = int(
        unit["unit_number"]
    )

    z_min = float(
        unit["z_min"]
    )

    z_max = float(
        unit["z_max"]
    )

    source_area = float(
        unit["area_m2"]
    )

    source_volume = float(
        unit["volume_m3"]
    )

    polygon = unit.geometry


    # ========================================================
    # GEOMETRY VALIDATION
    # ========================================================

    if polygon is None:
        raise ValueError(
            f"{unit_id}: geometry is None."
        )

    if polygon.is_empty:
        raise ValueError(
            f"{unit_id}: geometry is empty."
        )

    if not polygon.is_valid:
        raise ValueError(
            f"{unit_id}: geometry is invalid."
        )


    # ========================================================
    # CALCULATE EXPECTED VALUES
    # ========================================================

    geometric_area = polygon.area

    height = z_max - z_min

    expected_volume = (
        geometric_area * height
    )


    # ========================================================
    # AREA VALIDATION
    # ========================================================

    area_error = abs(
        geometric_area - source_area
    )

    if area_error > AREA_TOLERANCE_M2:
        raise ValueError(
            f"{unit_id}: area mismatch.\n"
            f"Calculated: {geometric_area}\n"
            f"Source:     {source_area}\n"
            f"Error:      {area_error}"
        )


    # ========================================================
    # 3D EXTRUSION
    # ========================================================

    mesh = extrude_property_unit(
        polygon,
        z_min,
        z_max,
    )


    # ========================================================
    # MESH VALIDATION
    # ========================================================

    if len(mesh.vertices) == 0:
        raise ValueError(
            f"{unit_id}: mesh has no vertices."
        )

    if len(mesh.faces) == 0:
        raise ValueError(
            f"{unit_id}: mesh has no faces."
        )


    # ========================================================
    # WATERTIGHT VALIDATION
    # ========================================================

    watertight = bool(
        mesh.is_watertight
    )

    if not watertight:
        raise ValueError(
            f"{unit_id}: mesh is not watertight."
        )


    # ========================================================
    # VOLUME VALIDATION
    # ========================================================

    mesh_volume = abs(
        float(mesh.volume)
    )

    if mesh_volume <= 0:
        raise ValueError(
            f"{unit_id}: invalid mesh volume."
        )


    # --------------------------------------------------------
    # Compare against calculated geometric volume
    # --------------------------------------------------------

    volume_error = abs(
        mesh_volume - expected_volume
    )

    if volume_error > VOLUME_TOLERANCE_M3:
        raise ValueError(
            f"{unit_id}: geometric volume mismatch.\n"
            f"Expected: {expected_volume}\n"
            f"Actual:   {mesh_volume}\n"
            f"Error:    {volume_error}"
        )


    # --------------------------------------------------------
    # Compare against source dataset
    # --------------------------------------------------------

    source_volume_error = abs(
        mesh_volume - source_volume
    )

    if source_volume_error > VOLUME_TOLERANCE_M3:
        raise ValueError(
            f"{unit_id}: source volume mismatch.\n"
            f"Source: {source_volume}\n"
            f"Mesh:   {mesh_volume}\n"
            f"Error:  {source_volume_error}"
        )


    # ========================================================
    # STORE
    # ========================================================

    unit_meshes.append(
        mesh
    )


    unit_metadata.append(
        {
            "unit_id": unit_id,
            "parcel_id": parcel_id,
            "building_id": building_id,
            "floor_id": floor_id,
            "floor_number": floor_number,
            "unit_number": unit_number,
            "unit_type": unit["unit_type"],

            "crs": CRS,

            "local_origin": {
                "x": ORIGIN_X,
                "y": ORIGIN_Y,
                "z": 0.0,
            },

            "z_min": z_min,
            "z_max": z_max,
            "height_m": height,

            "footprint_area_m2":
                geometric_area,

            "volume_m3":
                mesh_volume,

            "expected_volume_m3":
                expected_volume,

            "volume_error_m3":
                volume_error,

            "vertex_count":
                len(mesh.vertices),

            "face_count":
                len(mesh.faces),

            "watertight":
                watertight,
        }
    )


    # ========================================================
    # OUTPUT
    # ========================================================

    print(
        f"{unit_id:22} | "
        f"Z {z_min:6.2f}–{z_max:6.2f} | "
        f"Area {geometric_area:9,.2f} m² | "
        f"Volume {mesh_volume:11,.2f} m³ | "
        f"Watertight: {watertight}"
    )


# ============================================================
# VERIFY THAT EVERYTHING WAS GENERATED
# ============================================================

if len(unit_meshes) != EXPECTED_UNIT_COUNT:
    raise ValueError(
        f"Expected {EXPECTED_UNIT_COUNT} meshes, "
        f"generated {len(unit_meshes)}."
    )


# ============================================================
# COMBINE MESHES
# ============================================================

combined_mesh = (
    trimesh.util.concatenate(
        unit_meshes
    )
)


# ============================================================
# COMPONENT VALIDATION
# ============================================================

components = combined_mesh.split(
    only_watertight=False
)


if len(components) != EXPECTED_UNIT_COUNT:
    raise ValueError(
        f"Expected {EXPECTED_UNIT_COUNT} "
        f"independent 3D components but found "
        f"{len(components)}."
    )


# ============================================================
# TOTAL VOLUME
# ============================================================

individual_volume_total = sum(
    item["volume_m3"]
    for item in unit_metadata
)

combined_volume = abs(
    float(combined_mesh.volume)
)

combined_volume_error = abs(
    combined_volume -
    individual_volume_total
)

if combined_volume_error > VOLUME_TOLERANCE_M3:
    raise ValueError(
        f"Combined volume mismatch: "
        f"{combined_volume_error:.6f} m³"
    )


# ============================================================
# EXPORT 3D MODEL
# ============================================================

combined_mesh.export(
    OUTPUT_FILE
)


# ============================================================
# EXPORT METADATA
# ============================================================

metadata = {
    "dataset":
        "Synthetic 3D property units",

    "crs":
        CRS,

    "local_origin":
        {
            "x": ORIGIN_X,
            "y": ORIGIN_Y,
            "z": 0.0,
        },

    "unit_count":
        len(unit_metadata),

    "component_count":
        len(components),

    "combined_volume_m3":
        combined_volume,

    "individual_volume_total_m3":
        individual_volume_total,

    "combined_volume_error_m3":
        combined_volume_error,

    "units":
        unit_metadata,
}


with open(
    METADATA_FILE,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        metadata,
        file,
        indent=2,
    )


# ============================================================
# FINAL VALIDATION
# ============================================================

all_watertight = all(
    item["watertight"]
    for item in unit_metadata
)

if not all_watertight:
    raise ValueError(
        "Not all property-unit meshes "
        "are watertight."
    )


max_volume_error = max(
    item["volume_error_m3"]
    for item in unit_metadata
)


if max_volume_error > VOLUME_TOLERANCE_M3:
    raise ValueError(
        "Maximum volume error exceeds tolerance."
    )


unique_parcels = {
    item["parcel_id"]
    for item in unit_metadata
}

unique_buildings = {
    item["building_id"]
    for item in unit_metadata
}

unique_floors = {
    item["floor_id"]
    for item in unit_metadata
}


if len(unique_parcels) != 3:
    raise ValueError(
        "Expected 3 parcels."
    )

if len(unique_buildings) != 3:
    raise ValueError(
        "Expected 3 buildings."
    )

if len(unique_floors) != 15:
    raise ValueError(
        "Expected 15 floors."
    )


# ============================================================
# FINAL REPORT
# ============================================================

print()

print("=" * 70)
print("3D PROPERTY UNIT RECONSTRUCTION COMPLETE")
print("=" * 70)

print()

print(
    f"Property units:        {len(unit_metadata)}"
)

print(
    f"Parcels represented:   {len(unique_parcels)}"
)

print(
    f"Buildings represented:{len(unique_buildings)}"
)

print(
    f"Floors represented:    {len(unique_floors)}"
)

print()

print(
    f"3D components:         {len(components)}"
)

print(
    f"Combined vertices:     "
    f"{len(combined_mesh.vertices)}"
)

print(
    f"Combined faces:        "
    f"{len(combined_mesh.faces)}"
)

print(
    f"Combined volume:       "
    f"{combined_volume:,.2f} m³"
)

print(
    f"Maximum volume error:  "
    f"{max_volume_error:.6f} m³"
)

print()

print(
    f"3D model: {OUTPUT_FILE}"
)

print(
    f"Metadata: {METADATA_FILE}"
)

print()

print(
    "CRS validation:             PASSED"
)

print(
    "Unit count validation:      PASSED"
)

print(
    "3D extrusion:               PASSED"
)

print(
    "Mesh validation:            PASSED"
)

print(
    "Watertight validation:      PASSED"
)

print(
    "Volume validation:          PASSED"
)

print(
    "Hierarchy validation:       PASSED"
)

print()

print(
    "ALL 3D PROPERTY UNIT VALIDATIONS PASSED"
)