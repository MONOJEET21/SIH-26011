"""
Export real Bhunaksha Dag 546 geometry to KML
for visual inspection in Google Earth.

Source:
    data/real/bhunaksha/dag_546.geojson

Source CRS:
    EPSG:32646

Output CRS:
    EPSG:4326

Output:
    data/real/bhunaksha/dag_546.kml
"""

from pathlib import Path

import geopandas as gpd


# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "real"
    / "bhunaksha"
    / "dag_546.geojson"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "real"
    / "bhunaksha"
    / "dag_546.kml"
)


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():

    print("=" * 70)
    print("DAG 546 → GOOGLE EARTH KML")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    # Read Bhunaksha parcel
    gdf = gpd.read_file(INPUT_FILE)

    if gdf.empty:
        raise ValueError(
            "Dag 546 GeoJSON contains no features."
        )

    print()
    print("Input:")
    print(INPUT_FILE)

    print()
    print("Original CRS:")
    print(gdf.crs)

    # --------------------------------------------------------
    # Ensure correct source CRS
    # --------------------------------------------------------

    if gdf.crs is None:
        gdf = gdf.set_crs(
            "EPSG:32646",
            allow_override=True,
        )

    # --------------------------------------------------------
    # Convert to WGS84 for Google Earth
    # --------------------------------------------------------

    gdf = gdf.to_crs("EPSG:4326")

    print()
    print("Output CRS:")
    print(gdf.crs)

    # --------------------------------------------------------
    # Add useful display fields
    # --------------------------------------------------------

    if "name" not in gdf.columns:
        gdf["name"] = "Dag 546"

    if "description" not in gdf.columns:
        gdf["description"] = (
            "Real Bhunaksha cadastral parcel | "
            "Dag 546 | "
            "ULPIN 8456A2E5NVP0H0"
        )

    # --------------------------------------------------------
    # Export KML
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # GeoPandas needs KML support through Fiona/pyogrio.
    try:
        gdf.to_file(
            OUTPUT_FILE,
            driver="KML",
        )

    except Exception as error:

        print()
        print("KML export failed.")
        print()
        print("Error:")
        print(error)

        print()
        print(
            "If your GeoPandas installation does not support "
            "KML writing, install the KML driver dependency."
        )

        raise

    print()
    print("=" * 70)
    print("EXPORT COMPLETE")
    print("=" * 70)

    print()
    print("KML saved to:")
    print(OUTPUT_FILE)

    print()
    print(
        "Open this KML in Google Earth and compare "
        "the Dag 546 boundary with the satellite imagery."
    )


if __name__ == "__main__":
    main()