from pathlib import Path
import json

import geopandas as gpd
import trimesh
from shapely.geometry import Polygon
from shapely.ops import triangulate


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "study_area"
    / "buildings.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "outputs"
    / "3d"
)

CRS = "EPSG:32646"


# ============================================================
# LOCAL 3D ORIGIN
# ============================================================
#
# The source data uses UTM coordinates around:
#
# X ≈ 500000
# Y ≈ 2940000
#
# Keeping these huge coordinates directly inside a 3D engine
# is unnecessary at this stage and can create precision issues.
#
# Therefore we use a local origin.
#
# All generated mesh coordinates are:
#
# local_x = real_x - ORIGIN_X
# local_y = real_y - ORIGIN_Y
# local_z = real_z
#
# The origin is preserved in metadata so the geometry can later
# be positioned correctly in Cesium.
# ============================================================

ORIGIN_X = 500000.0
ORIGIN_Y = 2940000.0


# ============================================================
# LOAD BUILDINGS
# ============================================================

if not INPUT_FILE.exists():

    raise FileNotFoundError(
        f"Input file not found:\n{INPUT_FILE}"
    )


buildings = gpd.read_file(INPUT_FILE)


# ============================================================
# INPUT VALIDATION
# ============================================================

if buildings.empty:

    raise ValueError(
        "Buildings dataset is empty."
    )


if buildings.crs is None:

    raise ValueError(
        "Buildings dataset has no CRS."
    )


if str(buildings.crs) != CRS:

    raise ValueError(
        f"Unexpected CRS: {buildings.crs}. "
        f"Expected {CRS}."
    )


required_columns = [
    "building_id",
    "z_min",
    "z_max",
    "height_m",
]


for column in required_columns:

    if column not in buildings.columns:

        raise ValueError(
            f"Required column missing: {column}"
        )


if not buildings.geometry.is_valid.all():

    raise ValueError(
        "Invalid building geometry detected."
    )


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# HELPER: TRIANGULATE POLYGON
# ============================================================

def polygon_to_triangles(polygon: Polygon):

    """
    Convert a polygon into triangles.

    The current synthetic buildings are simple polygons,
    but this function provides a clean abstraction for
    the future geometry pipeline.
    """

    triangles = triangulate(polygon)

    valid_triangles = []

    for triangle in triangles:

        # Only keep triangles actually covered by the
        # source polygon.

        if polygon.covers(triangle):

            valid_triangles.append(triangle)

    return valid_triangles


# ============================================================
# HELPER: CREATE EXTRUDED MESH
# ============================================================

def extrude_polygon(
    polygon: Polygon,
    z_min: float,
    z_max: float,
):
    """
    Create a closed triangular mesh from a 2D polygon
    between z_min and z_max.
    """

    if z_max <= z_min:

        raise ValueError(
            f"Invalid vertical range: "
            f"{z_min} → {z_max}"
        )

    triangles = polygon_to_triangles(polygon)

    if not triangles:

        raise ValueError(
            "Polygon could not be triangulated."
        )

    vertices = []
    faces = []

    # --------------------------------------------------------
    # Bottom and top faces
    # --------------------------------------------------------

    for triangle in triangles:

        coords = list(triangle.exterior.coords)[:-1]

        if len(coords) != 3:

            raise ValueError(
                "Triangulation did not produce "
                "a triangular face."
            )

        base_index = len(vertices)

        # Bottom triangle
        for x, y in coords:

            vertices.append(
                [
                    x - ORIGIN_X,
                    y - ORIGIN_Y,
                    z_min,
                ]
            )

        faces.append(
            [
                base_index,
                base_index + 2,
                base_index + 1,
            ]
        )

        # Top triangle
        top_index = len(vertices)

        for x, y in coords:

            vertices.append(
                [
                    x - ORIGIN_X,
                    y - ORIGIN_Y,
                    z_max,
                ]
            )

        faces.append(
            [
                top_index,
                top_index + 1,
                top_index + 2,
            ]
        )

    # --------------------------------------------------------
    # Vertical side walls
    # --------------------------------------------------------

    exterior_coords = list(
        polygon.exterior.coords
    )

    for i in range(
        len(exterior_coords) - 1
    ):

        x1, y1 = exterior_coords[i]

        x2, y2 = exterior_coords[i + 1]

        base_index = len(vertices)

        vertices.extend(
            [
                [
                    x1 - ORIGIN_X,
                    y1 - ORIGIN_Y,
                    z_min,
                ],
                [
                    x2 - ORIGIN_X,
                    y2 - ORIGIN_Y,
                    z_min,
                ],
                [
                    x2 - ORIGIN_X,
                    y2 - ORIGIN_Y,
                    z_max,
                ],
                [
                    x1 - ORIGIN_X,
                    y1 - ORIGIN_Y,
                    z_max,
                ],
            ]
        )

        faces.append(
            [
                base_index,
                base_index + 1,
                base_index + 2,
            ]
        )

        faces.append(
            [
                base_index,
                base_index + 2,
                base_index + 3,
            ]
        )

    mesh = trimesh.Trimesh(
        vertices=vertices,
        faces=faces,
        process=True,
    )

    return mesh


# ============================================================
# PROCESS BUILDINGS
# ============================================================

building_metadata = []

combined_meshes = []

print("=" * 65)
print("3D BUILDING RECONSTRUCTION")
print("=" * 65)

print()

print(f"Input CRS: {buildings.crs}")
print(
    f"Local origin: "
    f"({ORIGIN_X}, {ORIGIN_Y})"
)

print()

for _, building in buildings.iterrows():

    building_id = building["building_id"]

    z_min = float(
        building["z_min"]
    )

    z_max = float(
        building["z_max"]
    )

    polygon = building.geometry

    # --------------------------------------------------------
    # Geometry type check
    # --------------------------------------------------------

    if not isinstance(
        polygon,
        Polygon
    ):

        raise ValueError(
            f"{building_id} is not a Polygon."
        )

    # --------------------------------------------------------
    # Create mesh
    # --------------------------------------------------------

    mesh = extrude_polygon(
        polygon,
        z_min,
        z_max,
    )

    # --------------------------------------------------------
    # Mesh validation
    # --------------------------------------------------------

    if len(mesh.vertices) == 0:

        raise ValueError(
            f"{building_id}: no vertices generated."
        )

    if len(mesh.faces) == 0:

        raise ValueError(
            f"{building_id}: no faces generated."
        )

    if not mesh.is_watertight:

        raise ValueError(
            f"{building_id}: mesh is not watertight."
        )

    if mesh.volume <= 0:

        raise ValueError(
            f"{building_id}: mesh volume is invalid."
        )

    # --------------------------------------------------------
    # Save individual building OBJ
    # --------------------------------------------------------

    building_output = (
        OUTPUT_DIR
        / f"{building_id}.obj"
    )

    mesh.export(
        building_output
    )

    # --------------------------------------------------------
    # Calculate expected volume
    # --------------------------------------------------------

    footprint_area = (
        polygon.area
    )

    expected_volume = (
        footprint_area
        * (z_max - z_min)
    )

    volume_error = abs(
        mesh.volume - expected_volume
    )

    # --------------------------------------------------------
    # Store metadata
    # --------------------------------------------------------

    building_metadata.append(
        {
            "building_id": building_id,
            "parcel_id": building["parcel_id"],
            "crs": CRS,
            "origin_x": ORIGIN_X,
            "origin_y": ORIGIN_Y,
            "z_min": z_min,
            "z_max": z_max,
            "height_m": float(
                building["height_m"]
            ),
            "footprint_area_m2": footprint_area,
            "expected_volume_m3": expected_volume,
            "mesh_volume_m3": float(
                mesh.volume
            ),
            "volume_error_m3": volume_error,
            "vertex_count": len(
                mesh.vertices
            ),
            "face_count": len(
                mesh.faces
            ),
            "watertight": bool(
                mesh.is_watertight
            ),
            "mesh_file": building_output.name,
        }
    )

    combined_meshes.append(
        mesh
    )

    print(
        f"{building_id} | "
        f"Z {z_min:.2f}–{z_max:.2f} m | "
        f"Vertices: {len(mesh.vertices)} | "
        f"Faces: {len(mesh.faces)} | "
        f"Volume: {mesh.volume:,.2f} m³ | "
        f"Watertight: {mesh.is_watertight}"
    )


# ============================================================
# COMBINED CITY/BLOCK MESH
# ============================================================

combined_mesh = trimesh.util.concatenate(
    combined_meshes
)


combined_output = (
    OUTPUT_DIR
    / "buildings_3d.obj"
)


combined_mesh.export(
    combined_output
)


# ============================================================
# METADATA OUTPUT
# ============================================================

metadata = {
    "crs": CRS,
    "local_origin": {
        "x": ORIGIN_X,
        "y": ORIGIN_Y,
        "z": 0.0,
    },
    "source_file": str(
        INPUT_FILE
    ),
    "building_count": len(
        building_metadata
    ),
    "buildings": building_metadata,
}


metadata_path = (
    OUTPUT_DIR
    / "buildings_3d_metadata.json"
)


with open(
    metadata_path,
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
    for item in building_metadata
)


max_volume_error = max(
    item["volume_error_m3"]
    for item in building_metadata
)


if not all_watertight:

    raise ValueError(
        "One or more generated building meshes "
        "are not watertight."
    )


if max_volume_error > 0.01:

    raise ValueError(
        "3D volume differs from expected "
        "extrusion volume by more than 0.01 m³."
    )


# ============================================================
# SUMMARY
# ============================================================

print()

print("=" * 65)
print("3D RECONSTRUCTION COMPLETE")
print("=" * 65)

print()

print(
    f"Buildings reconstructed: "
    f"{len(building_metadata)}"
)

print(
    f"Combined vertices: "
    f"{len(combined_mesh.vertices)}"
)

print(
    f"Combined faces: "
    f"{len(combined_mesh.faces)}"
)

print(
    f"Combined volume: "
    f"{combined_mesh.volume:,.2f} m³"
)

print(
    f"Maximum volume error: "
    f"{max_volume_error:.6f} m³"
)

print()

print(
    f"Combined mesh: "
    f"{combined_output}"
)

print(
    f"Metadata: "
    f"{metadata_path}"
)

print()

print("CRS validation:          PASSED")
print("Input geometry:          PASSED")
print("3D extrusion:            PASSED")
print("Mesh vertices:           PASSED")
print("Mesh faces:              PASSED")
print("Watertight validation:   PASSED")
print("Volume validation:       PASSED")

print()

print("ALL 3D BUILDING VALIDATIONS PASSED")