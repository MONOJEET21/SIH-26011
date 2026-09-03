"""
REAL DATA SPATIAL MATCHING
Bhunaksha cadastral parcel ↔ OpenStreetMap buildings

Purpose:
    Determine whether OSM building footprints spatially correspond
    to the real Bhunaksha cadastral parcel.

Pilot:
    Dag 546
    ULPIN: 8456A2E5NVP0H0
    CRS: EPSG:32646

Input:
    data/real/bhunaksha/dag_546.geojson
    data/real/osm/export.geojson

Output:
    data/real/analysis/dag_546_osm_building_matches.json

Important:
    This script does NOT assume that a nearby OSM building belongs
    to the parcel. A building is classified using actual geometry.
"""

from pathlib import Path
import json
import math

import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

BHUNAKSHA_FILE = (
    PROJECT_ROOT
    / "data"
    / "real"
    / "bhunaksha"
    / "dag_546.geojson"
)

OSM_FILE = (
    PROJECT_ROOT
    / "data"
    / "real"
    / "osm"
    / "export.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "real"
    / "analysis"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "dag_546_osm_building_matches.json"
)


# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

TARGET_CRS = "EPSG:32646"

# Classification thresholds.
#
# STRONG:
#   At least 50% of building area lies inside parcel
#
# PARTIAL:
#   At least 5% of building area intersects parcel
#
# NEARBY:
#   Building does not intersect parcel but is reasonably close.
#
STRONG_MATCH_THRESHOLD = 50.0
PARTIAL_MATCH_THRESHOLD = 5.0

# Useful for analysis only.
# We do NOT call a building a parcel building merely because
# it is nearby.
NEARBY_DISTANCE_M = 100.0


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def safe_float(value):
    """Convert a value to float where possible."""
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def geometry_area(geometry):
    """Return geometry area safely."""
    if geometry is None or geometry.is_empty:
        return 0.0

    return float(geometry.area)


def geometry_distance(geometry_a, geometry_b):
    """Return planar distance between two geometries."""
    if (
        geometry_a is None
        or geometry_b is None
        or geometry_a.is_empty
        or geometry_b.is_empty
    ):
        return None

    return float(geometry_a.distance(geometry_b))


def get_building_id(feature, fallback_index):
    """
    Extract an OSM building identifier.

    Priority:
        feature.id
        properties.id
        properties.osm_id
        properties["@id"]
        fallback index
    """

    feature_id = feature.get("id")

    if feature_id:
        return str(feature_id)

    properties = feature.get("properties") or {}

    for key in [
        "id",
        "osm_id",
        "@id",
        "building_id",
    ]:
        value = properties.get(key)

        if value is not None:
            return str(value)

    return f"osm_building_{fallback_index}"


def get_properties(feature):
    """Return feature properties safely."""
    properties = feature.get("properties")

    if isinstance(properties, dict):
        return properties

    return {}


def classify_match(
    percent_inside,
    intersection_area,
    distance_to_parcel,
):
    """
    Classify the spatial relationship.

    IMPORTANT:
        'strong_match' means geometry strongly overlaps
        the parcel. It does not establish legal ownership.

    Returns:
        strong_match
        partial_match
        nearby
        no_match
    """

    if percent_inside >= STRONG_MATCH_THRESHOLD:
        return "strong_match"

    if (
        intersection_area > 0
        and percent_inside >= PARTIAL_MATCH_THRESHOLD
    ):
        return "partial_match"

    if (
        intersection_area == 0
        and distance_to_parcel is not None
        and distance_to_parcel <= NEARBY_DISTANCE_M
    ):
        return "nearby"

    return "no_match"


# ---------------------------------------------------------------------
# LOAD BHUNAKSHA
# ---------------------------------------------------------------------

def load_bhunaksha():
    print()
    print("REAL PARCEL")
    print("-" * 70)

    if not BHUNAKSHA_FILE.exists():
        raise FileNotFoundError(
            f"Bhunaksha file not found:\n{BHUNAKSHA_FILE}"
        )

    parcels = gpd.read_file(BHUNAKSHA_FILE)

    if parcels.empty:
        raise ValueError(
            "Bhunaksha GeoJSON contains no features."
        )

    if parcels.crs is None:
        raise ValueError(
            "Bhunaksha GeoJSON has no CRS."
        )

    # The pilot file should already be EPSG:32646.
    if parcels.crs.to_string() != TARGET_CRS:
        print(
            f"  Reprojecting parcel "
            f"{parcels.crs} → {TARGET_CRS}"
        )
        parcels = parcels.to_crs(TARGET_CRS)

    parcel = parcels.iloc[0]

    geometry = parcel.geometry

    if geometry is None or geometry.is_empty:
        raise ValueError(
            "Bhunaksha parcel has empty geometry."
        )

    if not isinstance(
        geometry,
        (Polygon, MultiPolygon),
    ):
        raise ValueError(
            f"Unexpected parcel geometry type: "
            f"{geometry.geom_type}"
        )

    properties = parcel.to_dict()

    dag_number = (
        properties.get("dag")
        or properties.get("dag_no")
        or properties.get("parcel_id")
        or properties.get("TEXTPARCEL")
        or "546"
    )

    ulpin = (
        properties.get("ulpin")
        or properties.get("ULPIN")
        or "8456A2E5NVP0H0"
    )

    print(f"Dag:              {dag_number}")
    print(f"ULPIN:            {ulpin}")
    print(
        f"Area metadata:    "
        f"{geometry_area(geometry)} m²"
    )
    print(
        f"Geometry type:    "
        f"{geometry.geom_type}"
    )
    print(f"CRS:              {TARGET_CRS}")

    return parcels, parcel, geometry, str(dag_number), str(ulpin)


# ---------------------------------------------------------------------
# LOAD OSM
# ---------------------------------------------------------------------

def load_osm():
    print()
    print("OSM BUILDING DATA")
    print("-" * 70)

    if not OSM_FILE.exists():
        raise FileNotFoundError(
            f"OSM file not found:\n{OSM_FILE}"
        )

    buildings = gpd.read_file(OSM_FILE)

    if buildings.empty:
        raise ValueError(
            "OSM GeoJSON contains no building features."
        )

    if buildings.crs is None:
        print(
            "WARNING: OSM file has no CRS. "
            "Assuming EPSG:4326 because it was exported "
            "from Overpass Turbo."
        )

        buildings = buildings.set_crs(
            "EPSG:4326",
            allow_override=True,
        )

    if buildings.crs.to_string() != TARGET_CRS:
        buildings = buildings.to_crs(TARGET_CRS)

    print(f"Buildings loaded: {len(buildings)}")
    print(f"CRS:              {buildings.crs}")

    return buildings


# ---------------------------------------------------------------------
# MATCH
# ---------------------------------------------------------------------

def perform_matching(
    buildings,
    parcel_geometry,
    dag_number,
    ulpin,
):
    print()
    print("OSM BUILDING MATCHES")
    print("-" * 70)

    results = []

    strong_matches = []
    partial_matches = []
    nearby_buildings = []

    for index, building in buildings.iterrows():

        geometry = building.geometry

        building_id = get_building_id(
            building.to_dict(),
            index,
        )

        properties = {
            key: value
            for key, value in building.to_dict().items()
            if key != "geometry"
        }

        # -------------------------------------------------------------
        # Invalid / empty geometry
        # -------------------------------------------------------------

        if geometry is None or geometry.is_empty:

            result = {
                "building_id": building_id,
                "status": "invalid_geometry",
                "building_area_m2": 0.0,
                "intersection_area_m2": 0.0,
                "percent_inside_parcel": 0.0,
                "centroid_inside_parcel": False,
                "distance_to_parcel_m": None,
                "classification": "invalid_geometry",
                "osm_properties": properties,
            }

            results.append(result)

            print()
            print(f"Building: {building_id}")
            print("  ERROR: empty geometry")

            continue

        # -------------------------------------------------------------
        # Geometry calculations
        # -------------------------------------------------------------

        building_area = geometry_area(geometry)

        intersection = geometry.intersection(
            parcel_geometry
        )

        intersection_area = geometry_area(
            intersection
        )

        if building_area > 0:
            percent_inside = (
                intersection_area
                / building_area
                * 100.0
            )
        else:
            percent_inside = 0.0

        centroid = geometry.centroid

        centroid_inside = parcel_geometry.covers(
            centroid
        )

        distance_to_parcel = geometry_distance(
            geometry,
            parcel_geometry,
        )

        classification = classify_match(
            percent_inside=percent_inside,
            intersection_area=intersection_area,
            distance_to_parcel=distance_to_parcel,
        )

        # -------------------------------------------------------------
        # Result object
        # -------------------------------------------------------------

        result = {
            "building_id": building_id,

            "building_area_m2": round(
                building_area,
                3,
            ),

            "intersection_area_m2": round(
                intersection_area,
                3,
            ),

            "percent_inside_parcel": round(
                percent_inside,
                3,
            ),

            "centroid_inside_parcel": bool(
                centroid_inside
            ),

            "distance_to_parcel_m": (
                round(
                    distance_to_parcel,
                    3,
                )
                if distance_to_parcel is not None
                else None
            ),

            "classification": classification,

            "parcel_id": f"DAG_{dag_number}",

            "ulpin": ulpin,

            "osm_properties": properties,
        }

        results.append(result)

        # -------------------------------------------------------------
        # Categorize
        # -------------------------------------------------------------

        if classification == "strong_match":
            strong_matches.append(result)

        elif classification == "partial_match":
            partial_matches.append(result)

        elif classification == "nearby":
            nearby_buildings.append(result)

        # -------------------------------------------------------------
        # Console output
        # -------------------------------------------------------------

        print()
        print(f"Building: {building_id}")

        print(
            f"  Building area:       "
            f"{building_area:.3f} m²"
        )

        print(
            f"  Intersection area:   "
            f"{intersection_area:.3f} m²"
        )

        print(
            f"  % inside Dag {dag_number}:    "
            f"{percent_inside:.3f}%"
        )

        print(
            f"  Centroid inside:     "
            f"{centroid_inside}"
        )

        if distance_to_parcel is not None:
            print(
                f"  Distance to parcel:  "
                f"{distance_to_parcel:.3f} m"
            )
        else:
            print(
                "  Distance to parcel:  N/A"
            )

        print(
            f"  Classification:      "
            f"{classification}"
        )

    return (
        results,
        strong_matches,
        partial_matches,
        nearby_buildings,
    )


# ---------------------------------------------------------------------
# SAVE RESULTS
# ---------------------------------------------------------------------

def save_results(
    results,
    strong_matches,
    partial_matches,
    nearby_buildings,
    dag_number,
    ulpin,
    parcel_geometry,
    buildings,
):
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "metadata": {
            "analysis": (
                "Bhunaksha Dag 546 ↔ "
                "OpenStreetMap building spatial matching"
            ),
            "parcel_source": (
                "Assam Bhunaksha cadastral geometry"
            ),
            "building_source": (
                "OpenStreetMap / Overpass"
            ),
            "crs": TARGET_CRS,
            "dag": str(dag_number),
            "ulpin": str(ulpin),
            "parcel_geometry_type": (
                parcel_geometry.geom_type
            ),
            "parcel_geometry_area_m2": round(
                geometry_area(parcel_geometry),
                3,
            ),
            "osm_building_count": len(buildings),
            "strong_match_threshold_percent": (
                STRONG_MATCH_THRESHOLD
            ),
            "partial_match_threshold_percent": (
                PARTIAL_MATCH_THRESHOLD
            ),
            "nearby_distance_threshold_m": (
                NEARBY_DISTANCE_M
            ),
        },

        "summary": {
            "total_buildings": len(results),

            "strong_matches": len(
                strong_matches
            ),

            "partial_matches": len(
                partial_matches
            ),

            "nearby_buildings": len(
                nearby_buildings
            ),

            "no_matches": sum(
                1
                for result in results
                if result["classification"]
                == "no_match"
            ),

            "invalid_geometries": sum(
                1
                for result in results
                if result["classification"]
                == "invalid_geometry"
            ),
        },

        "results": results,

        "strong_matches": strong_matches,

        "partial_matches": partial_matches,

        "nearby_buildings": nearby_buildings,
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return OUTPUT_FILE


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():

    print("=" * 70)
    print("REAL DATA SPATIAL MATCH")
    print(
        "Bhunaksha Dag 546 ↔ OpenStreetMap Buildings"
    )
    print("=" * 70)

    # -------------------------------------------------------------
    # Load real cadastral parcel
    # -------------------------------------------------------------

    (
        parcels,
        parcel,
        parcel_geometry,
        dag_number,
        ulpin,
    ) = load_bhunaksha()

    # -------------------------------------------------------------
    # Load real OSM buildings
    # -------------------------------------------------------------

    buildings = load_osm()

    # -------------------------------------------------------------
    # Spatial matching
    # -------------------------------------------------------------

    (
        results,
        strong_matches,
        partial_matches,
        nearby_buildings,
    ) = perform_matching(
        buildings=buildings,
        parcel_geometry=parcel_geometry,
        dag_number=dag_number,
        ulpin=ulpin,
    )

    # -------------------------------------------------------------
    # Save
    # -------------------------------------------------------------

    output_file = save_results(
        results=results,
        strong_matches=strong_matches,
        partial_matches=partial_matches,
        nearby_buildings=nearby_buildings,
        dag_number=dag_number,
        ulpin=ulpin,
        parcel_geometry=parcel_geometry,
        buildings=buildings,
    )

    # -------------------------------------------------------------
    # Final report
    # -------------------------------------------------------------

    no_matches = sum(
        1
        for result in results
        if result["classification"]
        == "no_match"
    )

    print()
    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

    print("Results saved to:")
    print(output_file)

    print()
    print(
        f"Strong matches:   "
        f"{len(strong_matches)}"
    )

    print(
        f"Partial matches:  "
        f"{len(partial_matches)}"
    )

    print(
        f"Nearby buildings:  "
        f"{len(nearby_buildings)}"
    )

    print(
        f"No matches:        "
        f"{no_matches}"
    )

    print(
        f"Total buildings:   "
        f"{len(results)}"
    )

    # -------------------------------------------------------------
    # Useful interpretation
    # -------------------------------------------------------------

    print()
    print("INTERPRETATION")
    print("-" * 70)

    if strong_matches:
        print(
            "Strong spatial building candidates found."
        )

    elif partial_matches:
        print(
            "Partial spatial building candidates found."
        )

    elif nearby_buildings:
        print(
            "No building intersects Dag 546, "
            "but nearby OSM buildings were found."
        )

    else:
        print(
            "No OSM building has a spatial relationship "
            "with Dag 546 under the configured thresholds."
        )

    print()
    print(
        "IMPORTANT: A spatial match indicates geometric "
        "correspondence only. It does not establish legal "
        "ownership or cadastral authority."
    )


if __name__ == "__main__":
    main()