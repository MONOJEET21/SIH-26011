from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon


INPUT_DEFAULT = "data/real/buildings/Guwahati_3d_Buildings.gpkg"

OUTPUT_DIR = Path("data/outputs/real_3d_buildings")

FLOOR_METADATA = OUTPUT_DIR / "floors_3d_metadata.json"

OBJ_OUTPUT = OUTPUT_DIR / "property_units_3d.obj"
META_OUTPUT = OUTPUT_DIR / "property_units_3d_metadata.json"

WORKING_CRS = "EPSG:32646"

DEFAULT_UNITS_PER_FLOOR = 3


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
    value = safe_float(value)

    if value is None:
        return None

    return int(round(value))


def clean_string(value):
    if value is None:
        return None

    text = str(value).strip()

    if text.lower() in {"", "nan", "none", "null"}:
        return None

    return text


def polygon_parts(geometry):
    if geometry is None or geometry.is_empty:
        return []

    if geometry.geom_type == "Polygon":
        return [geometry]

    if geometry.geom_type == "MultiPolygon":
        return list(geometry.geoms)

    return []


def subdivide_polygon(polygon, units):
    """
    Deterministically divide a polygon into approximately equal
    vertical strips along its bounding-box X direction.

    This is a PROTOTYPE subdivision, not an official cadastral
    property-unit boundary.
    """

    if units <= 1:
        return [polygon]

    minx, miny, maxx, maxy = polygon.bounds

    width = maxx - minx

    if width <= 0:
        return [polygon]

    result = []

    for i in range(units):
        x1 = minx + width * (i / units)
        x2 = minx + width * ((i + 1) / units)

        cutter = Polygon(
            [
                (x1, miny - 1),
                (x2, miny - 1),
                (x2, maxy + 1),
                (x1, maxy + 1),
                (x1, miny - 1),
            ]
        )

        piece = polygon.intersection(cutter)

        if piece.is_empty:
            continue

        if piece.geom_type == "Polygon":
            result.append(piece)

        elif piece.geom_type == "MultiPolygon":
            # Keep the largest resulting polygon for deterministic
            # unit generation.
            largest = max(piece.geoms, key=lambda p: p.area)

            if not largest.is_empty:
                result.append(largest)

    return result


def add_box(vertices, faces, polygon, z_min, z_max):
    if polygon.is_empty:
        return

    if polygon.geom_type != "Polygon":
        return

    coords = list(polygon.exterior.coords)

    if len(coords) < 4:
        return

    if coords[0] == coords[-1]:
        coords = coords[:-1]

    if len(coords) < 3:
        return

    start = len(vertices)

    # Bottom vertices
    for x, y in coords:
        vertices.append((x, y, z_min))

    # Top vertices
    for x, y in coords:
        vertices.append((x, y, z_max))

    n = len(coords)

    # Bottom
    faces.append(
        tuple(
            start + i
            for i in reversed(range(n))
        )
    )

    # Top
    faces.append(
        tuple(
            start + n + i
            for i in range(n)
        )
    )

    # Sides
    for i in range(n):
        j = (i + 1) % n

        faces.append(
            (
                start + i,
                start + j,
                start + n + j,
                start + n + i,
            )
        )


def write_obj(path, vertices, faces):
    with path.open("w", encoding="utf-8") as f:

        f.write(
            "# 3D ULPIN prototype property-unit volumes\n"
        )

        for x, y, z in vertices:
            f.write(
                f"v {x:.6f} {y:.6f} {z:.6f}\n"
            )

        for face in faces:
            indices = [
                str(i + 1)
                for i in face
            ]

            f.write(
                "f " + " ".join(indices) + "\n"
            )


def main():

    input_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(INPUT_DEFAULT)
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    if not FLOOR_METADATA.exists():
        raise FileNotFoundError(
            f"Floor metadata not found: {FLOOR_METADATA}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(f"Reading buildings: {input_path}")

    gdf = gpd.read_file(input_path)

    if gdf.empty:
        raise RuntimeError(
            "Input building dataset is empty."
        )

    if gdf.crs is None:
        raise RuntimeError(
            "Input building dataset has no CRS."
        )

    gdf = gdf.to_crs(WORKING_CRS)

    print(f"Buildings available : {len(gdf)}")

    # ------------------------------------------------------------
    # BUILD STABLE INTERNAL BUILDING ID MAP
    # ------------------------------------------------------------

    building_lookup = {}

    for source_index, (_, row) in enumerate(
        gdf.iterrows(),
        start=1,
    ):

        building_id = f"GHY-B{source_index:06d}"

        building_lookup[building_id] = {
            "geometry": row.geometry,
            "source_osm_id": clean_string(
                row.get("osm_id")
            ),
            "source_name": clean_string(
                row.get("name")
            ),
            "source_type": clean_string(
                row.get("type")
            ),
            "source_levels": safe_int(
                row.get("building:levels")
            ),
            "source_height_m": safe_float(
                row.get("height")
            ),
        }

    # ------------------------------------------------------------
    # READ FLOOR METADATA
    # ------------------------------------------------------------

    with FLOOR_METADATA.open(
        "r",
        encoding="utf-8",
    ) as f:
        floor_metadata = json.load(f)

    floors = floor_metadata.get(
        "floors",
        [],
    )

    print(f"Input floors        : {len(floors)}")

    vertices = []
    faces = []
    units = []

    unit_count = 0

    missing_buildings = set()

    # ------------------------------------------------------------
    # GENERATE UNITS
    # ------------------------------------------------------------

    for floor in floors:

        building_id = floor.get(
            "building_id"
        )

        floor_id = floor.get(
            "floor_id"
        )

        if building_id not in building_lookup:

            missing_buildings.add(
                str(building_id)
            )

            continue

        building = building_lookup[
            building_id
        ]

        geometry = building["geometry"]

        if geometry is None or geometry.is_empty:
            continue

        z_min = safe_float(
            floor.get("z_min")
        )

        z_max = safe_float(
            floor.get("z_max")
        )

        if z_min is None or z_max is None:
            continue

        floor_number = safe_int(
            floor.get("floor_number")
        )

        if floor_number is None:
            floor_number = 1

        # --------------------------------------------------------
        # CREATE 3 PROTOTYPE UNITS PER FLOOR
        # --------------------------------------------------------

        parts = polygon_parts(
            geometry
        )

        if not parts:
            continue

        # For MultiPolygon footprints, divide each polygon,
        # then keep the largest three resulting areas.
        candidate_units = []

        for polygon in parts:

            subdivisions = subdivide_polygon(
                polygon,
                DEFAULT_UNITS_PER_FLOOR,
            )

            candidate_units.extend(
                subdivisions
            )

        candidate_units = [
            p
            for p in candidate_units
            if not p.is_empty
            and p.area > 0
        ]

        candidate_units.sort(
            key=lambda p: p.area,
            reverse=True,
        )

        candidate_units = candidate_units[
            :DEFAULT_UNITS_PER_FLOOR
        ]

        # If unusual geometry prevented 3 units,
        # use the original polygon as fallback.
        if not candidate_units:
            candidate_units = [parts[0]]

        for unit_index, unit_polygon in enumerate(
            candidate_units,
            start=1,
        ):

            unit_id = (
                f"{building_id}-"
                f"F{floor_number:02d}-"
                f"U{unit_index:02d}"
            )

            area_m2 = float(
                unit_polygon.area
            )

            height_m = float(
                z_max - z_min
            )

            volume_m3 = (
                area_m2 * height_m
            )

            before_vertices = len(vertices)
            before_faces = len(faces)

            add_box(
                vertices,
                faces,
                unit_polygon,
                z_min,
                z_max,
            )

            geometry_vertices = (
                len(vertices)
                - before_vertices
            )

            geometry_faces = (
                len(faces)
                - before_faces
            )

            units.append(
                {
                    "unit_id": unit_id,
                    "building_id": building_id,
                    "floor_id": floor_id,

                    "source_osm_id":
                        building["source_osm_id"],

                    "source_building_name":
                        building["source_name"],

                    "source_building_type":
                        building["source_type"],

                    "floor_number":
                        floor_number,

                    "unit_number":
                        unit_index,

                    "unit_type":
                        "PROTOTYPE_PROPERTY_UNIT",

                    "z_min":
                        z_min,

                    "z_max":
                        z_max,

                    "height_m":
                        height_m,

                    "area_m2":
                        area_m2,

                    "volume_m3":
                        volume_m3,

                    "geometry_vertex_count":
                        geometry_vertices,

                    "geometry_face_count":
                        geometry_faces,

                    "data_status":
                        "prototype_derived",
                }
            )

            unit_count += 1

    # ------------------------------------------------------------
    # WRITE OBJ
    # ------------------------------------------------------------

    write_obj(
        OBJ_OUTPUT,
        vertices,
        faces,
    )

    # ------------------------------------------------------------
    # WRITE METADATA
    # ------------------------------------------------------------

    metadata = {

        "dataset":
            "Guwahati Real Prototype Property Units",

        "version":
            "0.2.0",

        "source_building_file":
            str(input_path),

        "source_floor_metadata":
            str(FLOOR_METADATA),

        "working_crs":
            WORKING_CRS,

        "id_policy": {

            "building_id":
                "GHY-B######",

            "floor_id":
                "GHY-B######-F##",

            "property_unit_id":
                "GHY-B######-F##-U##",

            "source_identity":
                "osm_id",

            "source_identity_preserved_as":
                "source_osm_id",

            "primary_identity":
                "generated_internal_id",
        },

        "units_per_floor_requested":
            DEFAULT_UNITS_PER_FLOOR,

        "building_count":
            len(building_lookup),

        "floor_count":
            len(floors),

        "property_unit_count":
            unit_count,

        "vertex_count":
            len(vertices),

        "face_count":
            len(faces),

        "data_status":
            "prototype_derived",

        "authority_note":
            (
                "Property-unit boundaries are "
                "algorithmically subdivided from "
                "real building footprints. They "
                "are prototype spatial entities "
                "and are not official cadastral, "
                "ownership, tenancy, or ULPIN "
                "property-unit records."
            ),

        "units":
            units,
    }

    if missing_buildings:

        metadata["missing_building_ids"] = sorted(
            missing_buildings
        )

    with META_OUTPUT.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            metadata,
            f,
            indent=2,
        )

    # ------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------

    print()
    print("==========================================")
    print("3D PROPERTY UNIT GENERATION COMPLETE")
    print("==========================================")
    print(
        f"Buildings available : "
        f"{len(building_lookup)}"
    )
    print(
        f"Input floors        : "
        f"{len(floors)}"
    )
    print(
        f"Property units      : "
        f"{unit_count}"
    )
    print(
        f"Vertices            : "
        f"{len(vertices)}"
    )
    print(
        f"Faces               : "
        f"{len(faces)}"
    )
    print(
        f"OBJ                 : "
        f"{OBJ_OUTPUT}"
    )
    print(
        f"Metadata             : "
        f"{META_OUTPUT}"
    )

    if missing_buildings:
        print()
        print(
            "WARNING: Missing building IDs:"
        )

        for building_id in sorted(
            missing_buildings
        ):
            print(
                f"  {building_id}"
            )

    print("==========================================")


if __name__ == "__main__":
    main()