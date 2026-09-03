from pathlib import Path
import json

import geopandas as gpd
import trimesh
from shapely.geometry import box
from shapely.affinity import translate


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

PARCELS_FILE = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "study_area"
    / "parcels.geojson"
)

OUTPUT_2D = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "study_area"
    / "underground_assets.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "outputs"
    / "3d"
)

OUTPUT_3D = (
    OUTPUT_DIR
    / "underground_assets_3d.obj"
)

METADATA_FILE = (
    OUTPUT_DIR
    / "underground_assets_3d_metadata.json"
)

CRS = "EPSG:32646"

ORIGIN_X = 500000.0
ORIGIN_Y = 2940000.0


# ============================================================
# ASSET PARAMETERS
# ============================================================

ASSET_DEFINITIONS = [
    {
        "asset_id": "UA001",
        "asset_type": "WATER_PIPE",
        "asset_name": "Primary Water Supply",
        "parcel_id": "P001",
        "length_m": 80.0,
        "width_m": 2.0,
        "z_min": -4.0,
        "z_max": -3.0,
    },
    {
        "asset_id": "UA002",
        "asset_type": "ELECTRIC_DUCT",
        "asset_name": "Underground Electrical Corridor",
        "parcel_id": "P003",
        "length_m": 80.0,
        "width_m": 2.5,
        "z_min": -6.0,
        "z_max": -5.0,
    },
]


# ============================================================
# CREATE SAFE RECTANGULAR ASSET
# ============================================================

def create_asset_inside_parcel(
    parcel_geometry,
    length,
    width,
):
    """
    Create a rectangular asset using the actual
    bounding box of the parent parcel.

    The rectangle is deliberately inset from
    the parcel boundary.

    This prevents the synthetic generator from
    placing an asset outside its parent parcel.
    """

    minx, miny, maxx, maxy = (
        parcel_geometry.bounds
    )

    parcel_width = maxx - minx
    parcel_height = maxy - miny


    # --------------------------------------------------------
    # Safety checks
    # --------------------------------------------------------

    if length >= parcel_width:
        raise ValueError(
            f"Asset length {length} m is too large "
            f"for parcel width {parcel_width} m."
        )

    if width >= parcel_height:
        raise ValueError(
            f"Asset width {width} m is too large "
            f"for parcel height {parcel_height} m."
        )


    # --------------------------------------------------------
    # Center of parcel
    # --------------------------------------------------------

    center_x = (
        minx + maxx
    ) / 2.0

    center_y = (
        miny + maxy
    ) / 2.0


    # --------------------------------------------------------
    # Create centered rectangle
    # --------------------------------------------------------

    asset = box(
        center_x - length / 2.0,
        center_y - width / 2.0,
        center_x + length / 2.0,
        center_y + width / 2.0,
    )


    return asset


# ============================================================
# 3D EXTRUSION
# ============================================================

def extrude_asset(
    polygon,
    z_min,
    z_max,
):
    """
    Convert a 2D underground footprint into
    a watertight 3D solid.
    """

    if z_max <= z_min:
        raise ValueError(
            f"Invalid Z range: "
            f"{z_min} → {z_max}"
        )


    # --------------------------------------------------------
    # Move into local coordinate system
    # --------------------------------------------------------

    local_polygon = translate(
        polygon,
        xoff=-ORIGIN_X,
        yoff=-ORIGIN_Y,
    )


    height = (
        z_max - z_min
    )


    # --------------------------------------------------------
    # Extrude
    # --------------------------------------------------------

    mesh = trimesh.creation.extrude_polygon(
        local_polygon,
        height=height,
    )


    # --------------------------------------------------------
    # Move to actual depth
    # --------------------------------------------------------

    mesh.apply_translation(
        [
            0.0,
            0.0,
            z_min,
        ]
    )


    # --------------------------------------------------------
    # Clean
    # --------------------------------------------------------

    mesh.merge_vertices()

    mesh.process(
        validate=True
    )


    return mesh


# ============================================================
# LOAD PARCELS
# ============================================================

print("=" * 70)
print("SYNTHETIC UNDERGROUND ASSET GENERATION")
print("=" * 70)

print()

print(
    f"CRS: {CRS}"
)

print(
    f"Local origin: "
    f"({ORIGIN_X}, {ORIGIN_Y})"
)

print()

print(
    f"Underground assets: "
    f"{len(ASSET_DEFINITIONS)}"
)

print()


if not PARCELS_FILE.exists():
    raise FileNotFoundError(
        f"Parcel file not found:\n{PARCELS_FILE}"
    )


parcels = gpd.read_file(
    PARCELS_FILE
)


# ============================================================
# PARCEL VALIDATION
# ============================================================

if parcels.empty:
    raise ValueError(
        "Parcel dataset is empty."
    )


if parcels.crs is None:
    raise ValueError(
        "Parcel dataset has no CRS."
    )


if str(parcels.crs) != CRS:
    raise ValueError(
        f"Unexpected CRS: {parcels.crs}"
    )


if not parcels.geometry.is_valid.all():
    raise ValueError(
        "Parcel geometry is invalid."
    )


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# PROCESS ASSETS
# ============================================================

asset_records = []

asset_meshes = []

asset_metadata = []


for definition in ASSET_DEFINITIONS:

    asset_id = definition[
        "asset_id"
    ]

    asset_type = definition[
        "asset_type"
    ]

    asset_name = definition[
        "asset_name"
    ]

    parcel_id = definition[
        "parcel_id"
    ]

    length = float(
        definition["length_m"]
    )

    width = float(
        definition["width_m"]
    )

    z_min = float(
        definition["z_min"]
    )

    z_max = float(
        definition["z_max"]
    )


    # ========================================================
    # FIND PARENT PARCEL
    # ========================================================

    parent = parcels[
        parcels["parcel_id"] == parcel_id
    ]


    if parent.empty:
        raise ValueError(
            f"{asset_id}: parent parcel "
            f"{parcel_id} does not exist."
        )


    parent_geometry = (
        parent.geometry.iloc[0]
    )


    # ========================================================
    # CREATE ASSET FROM ACTUAL PARCEL EXTENT
    # ========================================================

    polygon = create_asset_inside_parcel(
        parent_geometry,
        length,
        width,
    )


    # ========================================================
    # GEOMETRY VALIDATION
    # ========================================================

    if polygon.is_empty:
        raise ValueError(
            f"{asset_id}: empty geometry."
        )


    if not polygon.is_valid:
        raise ValueError(
            f"{asset_id}: invalid geometry."
        )


    # ========================================================
    # PARENT PARCEL CONTAINMENT
    # ========================================================

    if not parent_geometry.contains(
        polygon
    ):
        raise ValueError(
            f"{asset_id}: underground asset "
            f"is outside parent parcel "
            f"{parcel_id}."
        )


    # ========================================================
    # GEOMETRIC VALUES
    # ========================================================

    area_m2 = polygon.area

    height = (
        z_max - z_min
    )

    expected_volume = (
        area_m2 * height
    )


    # ========================================================
    # 3D EXTRUSION
    # ========================================================

    mesh = extrude_asset(
        polygon,
        z_min,
        z_max,
    )


    # ========================================================
    # MESH VALIDATION
    # ========================================================

    if len(mesh.vertices) == 0:
        raise ValueError(
            f"{asset_id}: no mesh vertices."
        )


    if len(mesh.faces) == 0:
        raise ValueError(
            f"{asset_id}: no mesh faces."
        )


    watertight = bool(
        mesh.is_watertight
    )


    if not watertight:
        raise ValueError(
            f"{asset_id}: mesh is not watertight."
        )


    # ========================================================
    # VOLUME VALIDATION
    # ========================================================

    mesh_volume = abs(
        float(mesh.volume)
    )


    if mesh_volume <= 0:
        raise ValueError(
            f"{asset_id}: invalid mesh volume."
        )


    volume_error = abs(
        mesh_volume -
        expected_volume
    )


    if volume_error > 0.01:
        raise ValueError(
            f"{asset_id}: volume mismatch.\n"
            f"Expected: {expected_volume}\n"
            f"Actual: {mesh_volume}\n"
            f"Error: {volume_error}"
        )


    # ========================================================
    # STORE 2D RECORD
    # ========================================================

    asset_records.append(
        {
            "asset_id":
                asset_id,

            "asset_type":
                asset_type,

            "asset_name":
                asset_name,

            "parcel_id":
                parcel_id,

            "z_min":
                z_min,

            "z_max":
                z_max,

            "depth_min_m":
                abs(z_max),

            "depth_max_m":
                abs(z_min),

            "length_m":
                length,

            "width_m":
                width,

            "area_m2":
                area_m2,

            "volume_m3":
                mesh_volume,

            "geometry":
                polygon,
        }
    )


    # ========================================================
    # STORE MESH
    # ========================================================

    asset_meshes.append(
        mesh
    )


    # ========================================================
    # STORE METADATA
    # ========================================================

    asset_metadata.append(
        {
            "asset_id":
                asset_id,

            "asset_type":
                asset_type,

            "asset_name":
                asset_name,

            "parcel_id":
                parcel_id,

            "crs":
                CRS,

            "local_origin":
                {
                    "x": ORIGIN_X,
                    "y": ORIGIN_Y,
                    "z": 0.0,
                },

            "z_min":
                z_min,

            "z_max":
                z_max,

            "depth_min_m":
                abs(z_max),

            "depth_max_m":
                abs(z_min),

            "length_m":
                length,

            "width_m":
                width,

            "area_m2":
                area_m2,

            "volume_m3":
                mesh_volume,

            "watertight":
                watertight,

            "vertex_count":
                len(mesh.vertices),

            "face_count":
                len(mesh.faces),
        }
    )


    # ========================================================
    # PRINT
    # ========================================================

    print(
        f"{asset_id} | "
        f"{asset_type:18} | "
        f"Parcel {parcel_id} | "
        f"Depth {abs(z_max):5.1f}–"
        f"{abs(z_min):5.1f} m | "
        f"Length {length:6.1f} m | "
        f"Volume {mesh_volume:10,.2f} m³ | "
        f"Watertight: {watertight}"
    )


# ============================================================
# CREATE GEODATAFRAME
# ============================================================

underground_assets = gpd.GeoDataFrame(
    asset_records,
    geometry="geometry",
    crs=CRS,
)


# ============================================================
# ASSET OVERLAP VALIDATION
# ============================================================

for i in range(
    len(underground_assets)
):

    for j in range(
        i + 1,
        len(underground_assets)
    ):

        geometry_a = (
            underground_assets
            .geometry
            .iloc[i]
        )

        geometry_b = (
            underground_assets
            .geometry
            .iloc[j]
        )


        if geometry_a.intersects(
            geometry_b
        ):

            raise ValueError(
                "Underground assets overlap: "
                f"{underground_assets.asset_id.iloc[i]} "
                f"and "
                f"{underground_assets.asset_id.iloc[j]}"
            )


# ============================================================
# WRITE GEOJSON
# ============================================================

if OUTPUT_2D.exists():
    OUTPUT_2D.unlink()


underground_assets.to_file(
    OUTPUT_2D,
    driver="GeoJSON",
)


# ============================================================
# COMBINE 3D MESHES
# ============================================================

combined_mesh = (
    trimesh.util.concatenate(
        asset_meshes
    )
)


# ============================================================
# COMPONENT VALIDATION
# ============================================================

components = (
    combined_mesh.split(
        only_watertight=False
    )
)


if len(components) != 2:
    raise ValueError(
        f"Expected 2 3D components "
        f"but found {len(components)}."
    )


# ============================================================
# COMBINED VOLUME
# ============================================================

individual_volume = sum(
    item["volume_m3"]
    for item in asset_metadata
)


combined_volume = abs(
    float(combined_mesh.volume)
)


combined_volume_error = abs(
    combined_volume -
    individual_volume
)


if combined_volume_error > 0.01:
    raise ValueError(
        f"Combined volume mismatch: "
        f"{combined_volume_error}"
    )


# ============================================================
# EXPORT 3D MODEL
# ============================================================

if OUTPUT_3D.exists():
    OUTPUT_3D.unlink()


combined_mesh.export(
    OUTPUT_3D
)


# ============================================================
# EXPORT METADATA
# ============================================================

metadata = {

    "dataset":
        "Synthetic underground assets",

    "crs":
        CRS,

    "local_origin":
        {
            "x": ORIGIN_X,
            "y": ORIGIN_Y,
            "z": 0.0,
        },

    "asset_count":
        len(asset_metadata),

    "component_count":
        len(components),

    "combined_volume_m3":
        combined_volume,

    "volume_error_m3":
        combined_volume_error,

    "assets":
        asset_metadata,
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
    for item in asset_metadata
)


if not all_watertight:
    raise ValueError(
        "One or more underground assets "
        "are not watertight."
    )


print()

print("=" * 70)
print("UNDERGROUND ASSET GENERATION COMPLETE")
print("=" * 70)

print()

print(
    f"Assets generated:      "
    f"{len(asset_metadata)}"
)

print(
    f"3D components:          "
    f"{len(components)}"
)

print(
    f"Combined vertices:      "
    f"{len(combined_mesh.vertices)}"
)

print(
    f"Combined faces:         "
    f"{len(combined_mesh.faces)}"
)

print(
    f"Combined volume:        "
    f"{combined_volume:,.2f} m³"
)

print(
    f"Volume error:           "
    f"{combined_volume_error:.6f} m³"
)

print()

print(
    f"2D data: {OUTPUT_2D}"
)

print(
    f"3D model: {OUTPUT_3D}"
)

print(
    f"Metadata: {METADATA_FILE}"
)

print()

print(
    "CRS validation:          PASSED"
)

print(
    "Geometry validation:     PASSED"
)

print(
    "Parcel containment:      PASSED"
)

print(
    "Asset overlap:           PASSED"
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

print()

print(
    "ALL UNDERGROUND ASSET "
    "VALIDATIONS PASSED"
)