from pathlib import Path
import json
import math

import geopandas as gpd
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = Path(
    "data/real/buildings/Guwahati_3d_Buildings.gpkg"
)

OUTPUT_FILE = Path(
    "frontend/public/data/real/guwahati_buildings_3d.geojson"
)


# ============================================================
# HELPERS
# ============================================================

def clean_value(value):
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, float):
        if not math.isfinite(value):
            return None

    return value


def normalize_osm_id(value):
    value = clean_value(value)

    if value is None:
        return None

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(value)


def get_height(row):
    """
    Height policy:

    1. Existing source height
    2. building:levels * 3.2m
    3. 3.2m default
    """

    source_height = clean_value(
        row.get("height")
    )

    if source_height is not None:
        try:
            value = float(source_height)

            if value > 0:
                return round(value, 2), "source_height"

        except Exception:
            pass

    levels = clean_value(
        row.get("building:levels")
    )

    if levels is not None:
        try:
            value = float(levels)

            if value > 0:
                return round(value * 3.2, 2), "levels_x_3.2m"

        except Exception:
            pass

    return 3.2, "default_3.2m"


def get_levels(row, height_m):
    levels = clean_value(
        row.get("building:levels")
    )

    if levels is not None:
        try:
            value = int(round(float(levels)))

            if value > 0:
                return value, "source_levels"

        except Exception:
            pass

    estimated = max(
        1,
        int(round(height_m / 3.2))
    )

    return estimated, "height_divided_by_3.2m"


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("REAL GUWAHATI BUILDING WEB EXPORT")
    print("=" * 70)

    # --------------------------------------------------------
    # CHECK INPUT
    # --------------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"\nInput dataset not found:\n{INPUT_FILE}"
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # READ
    # --------------------------------------------------------

    print()
    print("Reading:")
    print(f"  {INPUT_FILE}")

    gdf = gpd.read_file(INPUT_FILE)

    print()
    print(f"Input features : {len(gdf)}")
    print(f"Input CRS      : {gdf.crs}")

    if len(gdf) == 0:
        raise RuntimeError(
            "The GeoPackage contains no features."
        )

    # --------------------------------------------------------
    # GEOMETRY VALIDATION
    # --------------------------------------------------------

    invalid_count = int(
        (~gdf.geometry.is_valid).sum()
    )

    if invalid_count > 0:

        print()
        print(
            f"Repairing {invalid_count} invalid geometries..."
        )

        gdf["geometry"] = (
            gdf.geometry
            .buffer(0)
        )

    # --------------------------------------------------------
    # CONVERT TO WEB CRS
    # --------------------------------------------------------

    if gdf.crs is None:
        raise RuntimeError(
            "Input dataset has no CRS."
        )

    gdf = gdf.to_crs(
        "EPSG:4326"
    )

    print(
        "Web CRS        : EPSG:4326"
    )

    # --------------------------------------------------------
    # CREATE FEATURES
    # --------------------------------------------------------

    features = []

    height_sources = {}

    for index, row in gdf.iterrows():

        # Stable internal project ID
        building_id = (
            f"GHY-B{index + 1:06d}"
        )

        # Source metadata
        source_osm_id = normalize_osm_id(
            row.get("osm_id")
        )

        source_name = clean_value(
            row.get("name")
        )

        source_type = clean_value(
            row.get("type")
        )

        source_levels = clean_value(
            row.get("building:levels")
        )

        source_height = clean_value(
            row.get("height")
        )

        # ----------------------------------------------------
        # DERIVED 3D INFORMATION
        # ----------------------------------------------------

        height_m, height_source = get_height(
            row
        )

        floors_estimated, floors_source = get_levels(
            row,
            height_m
        )

        height_sources[height_source] = (
            height_sources.get(
                height_source,
                0
            ) + 1
        )

        # ----------------------------------------------------
        # GEOMETRY
        # ----------------------------------------------------

        geometry = row.geometry

        if geometry is None or geometry.is_empty:
            print(
                f"Skipping {building_id}: empty geometry"
            )
            continue

        # ----------------------------------------------------
        # PROPERTIES
        # ----------------------------------------------------

        properties = {

            # Our project identity
            "building_id": building_id,

            # Original source identity
            "source_osm_id": source_osm_id,

            # Source metadata
            "source_name": source_name,
            "source_type": source_type,

            # Original source values
            "source_building_levels": source_levels,
            "source_height_m": source_height,

            # Derived 3D information
            "height_m": height_m,
            "floors_estimated": floors_estimated,

            # Provenance
            "height_source": height_source,
            "floors_source": floors_source,

            # Data classification
            "data_status": (
                "real_footprint_derived_height"
            ),

            "identity_status": (
                "prototype_internal_id"
            ),

            # UI-friendly name
            "display_name": (
                source_name
                if source_name
                else building_id
            ),
        }

        feature = {
            "type": "Feature",
            "id": building_id,
            "properties": properties,
            "geometry": geometry.__geo_interface__,
        }

        features.append(feature)

    # --------------------------------------------------------
    # GEOJSON
    # --------------------------------------------------------

    geojson = {

        "type": "FeatureCollection",

        "name": (
            "Guwahati Real 3D Buildings"
        ),

        "crs": {
            "type": "name",
            "properties": {
                "name": (
                    "urn:ogc:def:crs:OGC:1.3:CRS84"
                )
            }
        },

        "properties": {

            "dataset": (
                "Guwahati_3D_Buildings"
            ),

            "feature_count": len(features),

            "web_crs": "EPSG:4326",

            "height_policy": (
                "source height -> "
                "building levels x 3.2m -> "
                "3.2m default"
            ),

            "data_status": (
                "real_footprints_derived_3d_attributes"
            ),

            "identity_status": (
                "prototype_internal_building_ids"
            ),
        },

        "features": features,
    }

    # --------------------------------------------------------
    # WRITE
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            geojson,
            file,
            ensure_ascii=False,
            separators=(",", ":")
        )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("WEB EXPORT COMPLETE")
    print("=" * 70)

    print()
    print(
        f"Buildings exported : {len(features)}"
    )

    print()
    print("Height sources:")

    for source, count in sorted(
        height_sources.items()
    ):

        print(
            f"  {source:<30} {count}"
        )

    print()
    print("Output:")
    print(
        f"  {OUTPUT_FILE}"
    )

    print()
    print("First building IDs:")

    for feature in features[:5]:

        print(
            " ",
            feature["properties"]["building_id"]
        )

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()