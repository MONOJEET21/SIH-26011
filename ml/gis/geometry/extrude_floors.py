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
    / "floors.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "outputs"
    / "3d"
)

CRS = "EPSG:32646"


# ============================================================
# LOCAL COORDINATE ORIGIN
# ============================================================

ORIGIN_X = 500000.0
ORIGIN_Y = 2940000.0


# ============================================================
# LOAD FLOORS
# ============================================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Floor dataset not found:\n{INPUT_FILE}"
    )


floors = gpd.read_file(INPUT_FILE)


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
            f"Required column missing: {column}"
        )


if not floors.geometry.is_valid.all():

    raise ValueError(
        "Invalid floor geometry detected."
    )


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# POLYGON TRIANGULATION
# ============================================================

def polygon_to_triangles(
    polygon: Polygon
):
    """
    Convert a polygon into valid triangles.
    """

    triangles = triangulate(
        polygon
    )

    valid_triangles = []

    for triangle in triangles:

        if polygon.covers(
            triangle
        ):

            valid_triangles.append(
                triangle
            )

    return valid_triangles


# ============================================================
# POLYGON → CLOSED 3D SOLID
# ============================================================

def extrude_polygon(
    polygon: Polygon,
    z_min: float,
    z_max: float,
):
    """
    Convert a 2D polygon into a closed 3D
    triangular mesh between z_min and z_max.
    """

    if z_max <= z_min:

        raise ValueError(
            f"Invalid Z range: "
            f"{z_min} → {z_max}"
        )


    triangles = polygon_to_triangles(
        polygon
    )


    if not triangles:

        raise ValueError(
            "Polygon triangulation failed."
        )


    vertices = []
    faces = []


    # ========================================================
    # TOP + BOTTOM
    # ========================================================

    for triangle in triangles:

        coords = list(
            triangle.exterior.coords
        )[:-1]


        if len(coords) != 3:

            raise ValueError(
                "Expected triangular geometry."
            )


        # ----------------------------------------------------
        # Bottom triangle
        # ----------------------------------------------------

        bottom_index = len(
            vertices
        )


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
                bottom_index,
                bottom_index + 2,
                bottom_index + 1,
            ]
        )


        # ----------------------------------------------------
        # Top triangle
        # ----------------------------------------------------

        top_index = len(
            vertices
        )


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


    # ========================================================
    # SIDE WALLS
    # ========================================================

    exterior = list(
        polygon.exterior.coords
    )


    for i in range(
        len(exterior) - 1
    ):

        x1, y1 = exterior[i]

        x2, y2 = exterior[i + 1]


        wall_index = len(
            vertices
        )


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


        # First wall triangle
        faces.append(
            [
                wall_index,
                wall_index + 1,
                wall_index + 2,
            ]
        )


        # Second wall triangle
        faces.append(
            [
                wall_index,
                wall_index + 2,
                wall_index + 3,
            ]
        )


    # ========================================================
    # CREATE MESH
    # ========================================================

    mesh = trimesh.Trimesh(
        vertices=vertices,
        faces=faces,
        process=True,
    )


    return mesh


# ============================================================
# PROCESS FLOORS
# ============================================================

floor_metadata = []

floor_meshes = []


print("=" * 70)
print("3D FLOOR VOLUME RECONSTRUCTION")
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
    f"Floors to process: {len(floors)}"
)

print()


# ============================================================
# SORT FLOORS
# ============================================================

floors = floors.sort_values(
    [
        "building_id",
        "floor_number",
    ]
)


# ============================================================
# FLOOR LOOP
# ============================================================

for _, floor in floors.iterrows():

    floor_id = floor["floor_id"]

    building_id = floor[
        "building_id"
    ]

    parcel_id = floor[
        "parcel_id"
    ]

    floor_type = floor[
        "floor_type"
    ]

    z_min = float(
        floor["z_min"]
    )

    z_max = float(
        floor["z_max"]
    )

    polygon = floor.geometry


    # --------------------------------------------------------
    # Geometry type
    # --------------------------------------------------------

    if not isinstance(
        polygon,
        Polygon
    ):

        raise ValueError(
            f"{floor_id} is not a Polygon."
        )


    # --------------------------------------------------------
    # Generate volume
    # --------------------------------------------------------

    mesh = extrude_polygon(
        polygon,
        z_min,
        z_max,
    )


    # --------------------------------------------------------
    # Mesh validation
    # --------------------------------------------------------

    if len(
        mesh.vertices
    ) == 0:

        raise ValueError(
            f"{floor_id}: no vertices."
        )


    if len(
        mesh.faces
    ) == 0:

        raise ValueError(
            f"{floor_id}: no faces."
        )


    if not mesh.is_watertight:

        raise ValueError(
            f"{floor_id}: mesh is not watertight."
        )


    if mesh.volume <= 0:

        raise ValueError(
            f"{floor_id}: invalid volume."
        )


    # --------------------------------------------------------
    # Expected volume
    # --------------------------------------------------------

    footprint_area = (
        polygon.area
    )


    height = (
        z_max - z_min
    )


    expected_volume = (
        footprint_area
        * height
    )


    volume_error = abs(
        mesh.volume
        - expected_volume
    )


    # --------------------------------------------------------
    # Save OBJ
    # --------------------------------------------------------

    output_file = (
        OUTPUT_DIR
        / f"{floor_id}.obj"
    )


    mesh.export(
        output_file
    )


    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    metadata = {

        "floor_id": floor_id,

        "building_id": building_id,

        "parcel_id": parcel_id,

        "floor_number": int(
            floor["floor_number"]
        ),

        "floor_type": floor_type,

        "crs": CRS,

        "origin_x": ORIGIN_X,

        "origin_y": ORIGIN_Y,

        "z_min": z_min,

        "z_max": z_max,

        "height_m": height,

        "footprint_area_m2":
            footprint_area,

        "expected_volume_m3":
            expected_volume,

        "mesh_volume_m3":
            float(mesh.volume),

        "volume_error_m3":
            volume_error,

        "vertex_count":
            len(mesh.vertices),

        "face_count":
            len(mesh.faces),

        "watertight":
            bool(mesh.is_watertight),

        "mesh_file":
            output_file.name,
    }


    floor_metadata.append(
        metadata
    )


    floor_meshes.append(
        mesh
    )


    print(
        f"{floor_id:12} | "
        f"{floor_type:8} | "
        f"Z {z_min:6.2f}–{z_max:6.2f} | "
        f"Volume "
        f"{mesh.volume:10,.2f} m³ | "
        f"Watertight: "
        f"{mesh.is_watertight}"
    )


# ============================================================
# COMBINED FLOOR MODEL
# ============================================================

combined_mesh = (
    trimesh.util.concatenate(
        floor_meshes
    )
)


combined_file = (
    OUTPUT_DIR
    / "floors_3d.obj"
)


combined_mesh.export(
    combined_file
)


# ============================================================
# METADATA FILE
# ============================================================

metadata = {

    "dataset": (
        "Synthetic 3D cadastral floors"
    ),

    "crs": CRS,

    "local_origin": {

        "x": ORIGIN_X,

        "y": ORIGIN_Y,

        "z": 0.0,
    },

    "floor_count":
        len(floor_metadata),

    "floors":
        floor_metadata,
}


metadata_file = (
    OUTPUT_DIR
    / "floors_3d_metadata.json"
)


with open(
    metadata_file,
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
    for item in floor_metadata
)


max_volume_error = max(
    item["volume_error_m3"]
    for item in floor_metadata
)


if not all_watertight:

    raise ValueError(
        "One or more floor volumes "
        "are not watertight."
    )


if max_volume_error > 0.01:

    raise ValueError(
        "Floor volume validation failed. "
        "Maximum error exceeds 0.01 m³."
    )


# ============================================================
# SPECIAL BASEMENT VALIDATION
# ============================================================

basements = [
    item
    for item in floor_metadata
    if item["floor_type"]
    == "BASEMENT"
]


if len(basements) != 1:

    raise ValueError(
        "Expected exactly one basement."
    )


basement = basements[0]


if basement["z_max"] > 0:

    raise ValueError(
        "Basement must not extend "
        "above ground level."
    )


if basement["z_min"] >= 0:

    raise ValueError(
        "Basement must have "
        "negative Z extent."
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print()

print("=" * 70)
print("3D FLOOR RECONSTRUCTION COMPLETE")
print("=" * 70)

print()

print(
    f"Floor volumes generated: "
    f"{len(floor_metadata)}"
)

print(
    f"Standard floors: "
    f"{len(floor_metadata) - len(basements)}"
)

print(
    f"Basements: "
    f"{len(basements)}"
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
    f"{combined_file}"
)

print(
    f"Metadata: "
    f"{metadata_file}"
)

print()

print(
    "CRS validation:          PASSED"
)

print(
    "Floor geometry:          PASSED"
)

print(
    "3D extrusion:            PASSED"
)

print(
    "Watertight validation:   PASSED"
)

print(
    "Volume validation:       PASSED"
)

print(
    "Basement validation:     PASSED"
)

print()

print(
    "ALL 3D FLOOR VALIDATIONS PASSED"
)