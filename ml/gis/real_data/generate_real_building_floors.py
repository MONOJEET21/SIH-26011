from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon


INPUT_DEFAULT = "data/real/buildings/Guwahati_3d_Buildings.gpkg"

OUTPUT_DIR = Path("data/outputs/real_3d_buildings")
OBJ_OUTPUT = OUTPUT_DIR / "floors_3d.obj"
META_OUTPUT = OUTPUT_DIR / "floors_3d_metadata.json"

WORKING_CRS = "EPSG:32646"

FLOOR_HEIGHT_M = 3.2


def safe_float(value):
    try:
        if value is None:
            return None

        if hasattr(value, "item"):
            value = value.item()

        if isinstance(value, float) and value != value:
            return None

        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value):
    number = safe_float(value)

    if number is None:
        return None

    return int(round(number))


def clean_string(value):
    if value is None:
        return None

    text = str(value).strip()

    if text.lower() in {"", "nan", "none", "null"}:
        return None

    return text


def get_levels(row):
    levels = safe_int(row.get("building:levels"))

    if levels is not None and levels > 0:
        return levels, "source"

    height = safe_float(row.get("height"))

    if height is not None and height > 0:
        estimated = max(1, int(round(height / FLOOR_HEIGHT_M)))
        return estimated, "height_estimated"

    return 1, "default"


def add_box(vertices, faces, polygon, z_min, z_max):
    """
    Add a prism for a polygon.

    Returns the number of vertices/faces added.
    """

    if polygon.is_empty:
        return

    if polygon.geom_type != "Polygon":
        return

    coords = list(polygon.exterior.coords)

    if len(coords) < 4:
        return

    # Remove duplicate closing coordinate.
    if coords[0] == coords[-1]:
        coords = coords[:-1]

    if len(coords) < 3:
        return

    base_start = len(vertices)

    for x, y in coords:
        vertices.append((x, y, z_min))

    for x, y in coords:
        vertices.append((x, y, z_max))

    n = len(coords)

    # Bottom
    faces.append(tuple(base_start + i for i in reversed(range(n))))

    # Top
    faces.append(tuple(base_start + n + i for i in range(n)))

    # Sides
    for i in range(n):
        j = (i + 1) % n

        faces.append(
            (
                base_start + i,
                base_start + j,
                base_start + n + j,
                base_start + n + i,
            )
        )


def process_geometry(geometry, z_min, z_max, vertices, faces):
    if geometry is None or geometry.is_empty:
        return

    if geometry.geom_type == "Polygon":
        add_box(vertices, faces, geometry, z_min, z_max)

    elif geometry.geom_type == "MultiPolygon":
        for polygon in geometry.geoms:
            add_box(vertices, faces, polygon, z_min, z_max)


def write_obj(path, vertices, faces):
    with path.open("w", encoding="utf-8") as f:
        f.write("# 3D ULPIN derived building floor volumes\n")

        for x, y, z in vertices:
            f.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")

        for face in faces:
            # OBJ is 1-based.
            indices = [str(i + 1) for i in face]
            f.write("f " + " ".join(indices) + "\n")


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(INPUT_DEFAULT)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reading: {input_path}")

    gdf = gpd.read_file(input_path)

    if gdf.empty:
        raise RuntimeError("Input building dataset is empty.")

    if gdf.crs is None:
        raise RuntimeError("Input dataset has no CRS.")

    print(f"Input features : {len(gdf)}")
    print(f"Input CRS      : {gdf.crs}")

    # Reproject to metric CRS.
    gdf = gdf.to_crs(WORKING_CRS)

    vertices = []
    faces = []
    floors = []

    building_count = 0
    floor_count = 0

    for source_index, (_, row) in enumerate(gdf.iterrows(), start=1):

        # ------------------------------------------------------------
        # STABLE INTERNAL ID
        # ------------------------------------------------------------
        building_id = f"GHY-B{source_index:06d}"

        # ------------------------------------------------------------
        # ORIGINAL SOURCE IDENTIFIERS
        # ------------------------------------------------------------
        source_osm_id = clean_string(row.get("osm_id"))
        source_name = clean_string(row.get("name"))
        source_type = clean_string(row.get("type"))

        source_levels = safe_int(row.get("building:levels"))
        source_height = safe_float(row.get("height"))

        geometry = row.geometry

        if geometry is None or geometry.is_empty:
            print(f"WARNING: empty geometry for {building_id}")
            continue

        # ------------------------------------------------------------
        # DETERMINE FLOOR COUNT
        # ------------------------------------------------------------
        floor_count_for_building, level_method = get_levels(row)

        if floor_count_for_building < 1:
            floor_count_for_building = 1

        # Height policy:
        #
        # 1. Explicit source height
        # 2. building:levels × 3.2 m
        # 3. one floor × 3.2 m
        #
        if source_height is not None and source_height > 0:
            total_height = source_height
            height_method = "source_height"

        else:
            total_height = floor_count_for_building * FLOOR_HEIGHT_M
            height_method = "levels_estimated_height"

        actual_floor_height = total_height / floor_count_for_building

        building_count += 1

        # ------------------------------------------------------------
        # GENERATE FLOOR VOLUMES
        # ------------------------------------------------------------
        for floor_number in range(1, floor_count_for_building + 1):

            z_min = (floor_number - 1) * actual_floor_height
            z_max = floor_number * actual_floor_height

            floor_id = f"{building_id}-F{floor_number:02d}"

            before_vertices = len(vertices)
            before_faces = len(faces)

            process_geometry(
                geometry,
                z_min,
                z_max,
                vertices,
                faces,
            )

            floor_vertices = len(vertices) - before_vertices
            floor_faces = len(faces) - before_faces

            floors.append(
                {
                    "floor_id": floor_id,
                    "building_id": building_id,
                    "source_osm_id": source_osm_id,
                    "source_name": source_name,
                    "source_type": source_type,
                    "floor_number": floor_number,
                    "floor_type": "ABOVE_GROUND",
                    "floor_height_m": actual_floor_height,
                    "z_min": z_min,
                    "z_max": z_max,
                    "building_levels_source": source_levels,
                    "building_height_source_m": source_height,
                    "height_method": height_method,
                    "level_count_method": level_method,
                    "geometry_vertex_count": floor_vertices,
                    "geometry_face_count": floor_faces,
                    "data_status": "prototype_derived",
                }
            )

            floor_count += 1

    # ------------------------------------------------------------
    # WRITE OBJ
    # ------------------------------------------------------------

    write_obj(
        OBJ_OUTPUT,
        vertices,
        faces,
    )

    # ------------------------------------------------------------
    # METADATA
    # ------------------------------------------------------------

    metadata = {
        "dataset": "Guwahati Real Building Floors",
        "version": "0.2.0",
        "source_building_file": str(input_path),
        "working_crs": WORKING_CRS,

        "id_policy": {
            "building_id": "GHY-B######",
            "floor_id": "GHY-B######-F##",
            "primary_identity_source": "generated_internal_id",
            "source_identity_field": "osm_id",
            "source_identity_preserved_as": "source_osm_id",
        },

        "height_policy": {
            "explicit_height": "Use source height when available.",
            "levels_fallback": "building:levels × 3.2m",
            "default": "1 × 3.2m",
            "default_floor_height_m": FLOOR_HEIGHT_M,
        },

        "data_status": "prototype_derived",

        "authority_note": (
            "Building footprints and source attributes originate from the "
            "provided real/open building dataset. Floor volumes are "
            "algorithmically derived and are not authoritative cadastral "
            "floor records."
        ),

        "counts": {
            "input_features": len(gdf),
            "buildings_processed": building_count,
            "floor_count": floor_count,
            "vertex_count": len(vertices),
            "face_count": len(faces),
        },

        "floors": floors,
    }

    with META_OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print()
    print("==========================================")
    print("3D FLOOR GENERATION COMPLETE")
    print("==========================================")
    print(f"Buildings processed : {building_count}")
    print(f"Floor volumes       : {floor_count}")
    print(f"Vertices            : {len(vertices)}")
    print(f"Faces               : {len(faces)}")
    print(f"OBJ                 : {OBJ_OUTPUT}")
    print(f"Metadata             : {META_OUTPUT}")
    print("==========================================")


if __name__ == "__main__":
    main()