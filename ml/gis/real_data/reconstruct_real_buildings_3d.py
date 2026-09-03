from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon


def parse_number(value):
    if value is None:
        return None
    match = re.search(r"[-+]?\d+(?:\.\d+)?", str(value))
    return float(match.group()) if match else None


def polygons(geom):
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    return []


def main():
    parser = argparse.ArgumentParser(description="Build generic 3D building massing from footprint + height/levels data.")
    parser.add_argument("input", help="Input GeoPackage/GeoJSON containing building footprints")
    parser.add_argument("--output-dir", default="data/outputs/real_3d_buildings")
    parser.add_argument("--height-field", default="height")
    parser.add_argument("--levels-field", default="building:levels")
    parser.add_argument("--id-field", default="property_id")
    parser.add_argument("--default-floor-height", type=float, default=3.2)
    parser.add_argument("--working-crs", default="EPSG:32646")
    args = parser.parse_args()

    src = Path(args.input)
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_file(src)
    if gdf.empty:
        raise SystemExit("Input contains no features.")
    if gdf.crs is None:
        raise SystemExit("Input has no CRS; assign the correct CRS before running.")

    metric = gdf.to_crs(args.working_crs)
    minx, miny, maxx, maxy = metric.total_bounds
    ox, oy = (minx + maxx) / 2.0, (miny + maxy) / 2.0

    vertices = []
    faces = []
    metadata = []
    next_vertex = 1

    for idx, row in gdf.iterrows():
        height = parse_number(row.get(args.height_field))
        levels = parse_number(row.get(args.levels_field))

        if height is not None and height > 0:
            height_used = height
            method = "explicit_height"
            estimated_levels = max(1, round(height / args.default_floor_height))
        elif levels is not None and levels > 0:
            estimated_levels = max(1, round(levels))
            height_used = estimated_levels * args.default_floor_height
            method = "levels_estimated_height"
        else:
            estimated_levels = 1
            height_used = args.default_floor_height
            method = "default_estimated_height"

        source_id = row.get(args.id_field)
        if source_id is None or str(source_id).strip() == "":
            source_id = row.get("osm_id")
        if source_id is None or str(source_id).strip() == "":
            source_id = f"BUILDING-{idx + 1:06d}"
        building_id = str(source_id)

        geom = metric.loc[idx, "geometry"]
        part_index = 0
        for poly in polygons(geom):
            if poly.is_empty or poly.area <= 0:
                continue

            ring = list(poly.exterior.coords)[:-1]
            base = []
            top = []
            for x, y in ring:
                vertices.append((x - ox, y - oy, 0.0))
                base.append(next_vertex)
                next_vertex += 1
            for x, y in ring:
                vertices.append((x - ox, y - oy, height_used))
                top.append(next_vertex)
                next_vertex += 1

            faces.append(tuple(reversed(base)))
            faces.append(tuple(top))
            for j in range(len(ring)):
                k = (j + 1) % len(ring)
                faces.append((base[j], base[k], top[k], top[j]))

            metadata.append({
                "building_id": building_id,
                "source_index": int(idx),
                "osm_id": None if row.get("osm_id") is None else str(row.get("osm_id")),
                "name": None if row.get("name") is None else str(row.get("name")),
                "type": None if row.get("type") is None else str(row.get("type")),
                "levels_source": levels,
                "height_source_m": height,
                "height_used_m": height_used,
                "estimated_levels": estimated_levels,
                "height_method": method,
                "footprint_area_m2": float(poly.area),
                "part_index": part_index,
            })
            part_index += 1

    obj_path = outdir / "buildings_3d.obj"
    with obj_path.open("w", encoding="utf-8") as f:
        f.write("# 3D ULPIN real building massing\n")
        f.write(f"# Working CRS: {args.working_crs}\n")
        f.write(f"# Local origin UTM: E={ox}, N={oy}\n")
        for x, y, z in vertices:
            f.write(f"v {x:.3f} {y:.3f} {z:.3f}\n")
        for face in faces:
            f.write("f " + " ".join(map(str, face)) + "\n")

    meta_path = outdir / "buildings_3d_metadata.json"
    payload = {
        "source_file": str(src),
        "source_crs": str(gdf.crs),
        "working_crs": args.working_crs,
        "local_origin_utm": {"easting_m": ox, "northing_m": oy},
        "building_feature_count": int(len(gdf)),
        "mesh_part_count": len(metadata),
        "vertex_count": len(vertices),
        "face_count": len(faces),
        "height_policy": {
            "1": "Use explicit height when available",
            "2": "Otherwise use building levels × default floor height",
            "3": "Otherwise use default floor height and mark as estimated",
        },
        "default_floor_height_m": args.default_floor_height,
        "buildings": metadata,
    }
    meta_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Input features : {len(gdf)}")
    print(f"3D mesh parts  : {len(metadata)}")
    print(f"Vertices       : {len(vertices)}")
    print(f"Faces          : {len(faces)}")
    print(f"OBJ            : {obj_path}")
    print(f"Metadata       : {meta_path}")


if __name__ == "__main__":
    main()
