"""
REAL DATA SPATIAL MATCHING

Bhunaksha Dag 546
        ↕
Overture Maps Buildings

Purpose:
    Determine whether Overture building footprints overlap
    the real Bhunaksha cadastral parcel.

Sources:
    Bhunaksha:
        data/real/bhunaksha/dag_546.geojson

    Overture:
        data/real/overture/dag_546_buildings.geojson

Output:
    data/real/analysis/dag_546_overture_building_matches.json

IMPORTANT:
    A spatial overlap indicates geometric correspondence only.
    It does NOT establish legal ownership or cadastral authority.
"""

from pathlib import Path
import json

import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon


# ================================================================
# PATHS
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

BHUNAKSHA_FILE = (
    PROJECT_ROOT
    / "data"
    / "real"
    / "bhunaksha"
    / "dag_546.geojson"
)

OVERTURE_FILE = (
    PROJECT_ROOT
    / "data"
    / "real"
    / "overture"
    / "dag_546_buildings.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "real"
    / "analysis"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "dag_546_overture_building_matches.json"
)

TARGET_CRS = "EPSG:32646"

STRONG_THRESHOLD = 50.0
PARTIAL_THRESHOLD = 5.0
NEARBY_DISTANCE_M = 100.0


# ================================================================
# HELPERS
# ================================================================

def area(geometry):
    if geometry is None or geometry.is_empty:
        return 0.0

    return float(geometry.area)


def distance(a, b):
    if (
        a is None
        or b is None
        or a.is_empty
        or b.is_empty
    ):
        return None

    return float(a.distance(b))


def classify(
    percent_inside,
    intersection_area,
    distance_to_parcel,
):
    if percent_inside >= STRONG_THRESHOLD:
        return "strong_match"

    if (
        intersection_area > 0
        and percent_inside >= PARTIAL_THRESHOLD
    ):
        return "partial_match"

    if (
        intersection_area == 0
        and distance_to_parcel is not None
        and distance_to_parcel <= NEARBY_DISTANCE_M
    ):
        return "nearby"

    return "no_match"


# ================================================================
# LOAD BHUNAKSHA
# ================================================================

def load_parcel():

    print()
    print("REAL BHUNAKSHA PARCEL")
    print("-" * 70)

    if not BHUNAKSHA_FILE.exists():
        raise FileNotFoundError(
            f"Missing Bhunaksha file:\n{BHUNAKSHA_FILE}"
        )

    gdf = gpd.read_file(BHUNAKSHA_FILE)

    if gdf.empty:
        raise ValueError(
            "Bhunaksha file contains no features."
        )

    if gdf.crs is None:
        raise ValueError(
            "Bhunaksha file has no CRS."
        )

    if gdf.crs.to_string() != TARGET_CRS:
        gdf = gdf.to_crs(TARGET_CRS)

    parcel = gdf.iloc[0]

    geometry = parcel.geometry

    if geometry is None or geometry.is_empty:
        raise ValueError(
            "Dag 546 has empty geometry."
        )

    if not isinstance(
        geometry,
        (Polygon, MultiPolygon),
    ):
        raise ValueError(
            f"Unexpected parcel geometry: "
            f"{geometry.geom_type}"
        )

    properties = parcel.to_dict()

    dag = (
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

    print(f"Dag:              {dag}")
    print(f"ULPIN:            {ulpin}")
    print(
        f"Parcel area:      "
        f"{area(geometry):.3f} m²"
    )
    print(
        f"Geometry:         "
        f"{geometry.geom_type}"
    )
    print(f"CRS:              {TARGET_CRS}")

    return geometry, str(dag), str(ulpin)


# ================================================================
# LOAD OVERTURE
# ================================================================

def load_overture():

    print()
    print("OVERTURE BUILDINGS")
    print("-" * 70)

    if not OVERTURE_FILE.exists():
        raise FileNotFoundError(
            f"Missing Overture file:\n{OVERTURE_FILE}"
        )

    buildings = gpd.read_file(OVERTURE_FILE)

    if buildings.empty:
        raise ValueError(
            "Overture file contains no features."
        )

    if buildings.crs is None:
        raise ValueError(
            "Overture file has no CRS."
        )

    print(
        f"Buildings loaded: {len(buildings)}"
    )

    print(
        f"Original CRS:     {buildings.crs}"
    )

    if buildings.crs.to_string() != TARGET_CRS:
        buildings = buildings.to_crs(TARGET_CRS)

    print(
        f"Analysis CRS:     {buildings.crs}"
    )

    return buildings


# ================================================================
# MATCH BUILDINGS
# ================================================================

def match_buildings(
    buildings,
    parcel_geometry,
    dag,
    ulpin,
):

    print()
    print("OVERTURE → DAG 546 SPATIAL MATCHES")
    print("-" * 70)

    results = []

    strong = []
    partial = []
    nearby = []
    no_match = []

    for index, row in buildings.iterrows():

        geometry = row.geometry

        building_id = str(
            row.get("id")
            or f"overture_building_{index}"
        )

        # --------------------------------------------------------
        # Invalid geometry
        # --------------------------------------------------------

        if (
            geometry is None
            or geometry.is_empty
        ):

            result = {
                "building_id": building_id,
                "classification": "invalid_geometry",
                "building_area_m2": 0.0,
                "intersection_area_m2": 0.0,
                "percent_inside_parcel": 0.0,
                "centroid_inside_parcel": False,
                "distance_to_parcel_m": None,
                "parcel_id": f"DAG_{dag}",
                "ulpin": ulpin,
            }

            results.append(result)

            print()
            print(
                f"Building: {building_id}"
            )
            print(
                "  INVALID GEOMETRY"
            )

            continue

        # --------------------------------------------------------
        # Geometry measurements
        # --------------------------------------------------------

        building_area = area(geometry)

        intersection = geometry.intersection(
            parcel_geometry
        )

        intersection_area = area(
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

        distance_to_parcel = distance(
            geometry,
            parcel_geometry,
        )

        classification = classify(
            percent_inside,
            intersection_area,
            distance_to_parcel,
        )

        # --------------------------------------------------------
        # Preserve Overture metadata
        # --------------------------------------------------------

        source_metadata = {}

        for key in [
            "sources",
            "is_underground",
            "has_parts",
            "version",
        ]:

            if key in row:
                value = row[key]

                try:
                    json.dumps(value)
                    source_metadata[key] = value
                except TypeError:
                    source_metadata[key] = str(value)

        # --------------------------------------------------------
        # Result
        # --------------------------------------------------------

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

            "parcel_id": f"DAG_{dag}",

            "ulpin": ulpin,

            "source": "Overture Maps Buildings",

            "source_metadata": source_metadata,
        }

        results.append(result)

        # --------------------------------------------------------
        # Categorize
        # --------------------------------------------------------

        if classification == "strong_match":
            strong.append(result)

        elif classification == "partial_match":
            partial.append(result)

        elif classification == "nearby":
            nearby.append(result)

        else:
            no_match.append(result)

        # --------------------------------------------------------
        # Console
        # --------------------------------------------------------

        print()
        print(
            f"Building: {building_id}"
        )

        print(
            f"  Building area:       "
            f"{building_area:.3f} m²"
        )

        print(
            f"  Intersection area:   "
            f"{intersection_area:.3f} m²"
        )

        print(
            f"  % inside Dag {dag}:   "
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
        strong,
        partial,
        nearby,
        no_match,
    )


# ================================================================
# SAVE
# ================================================================

def save_results(
    results,
    strong,
    partial,
    nearby,
    no_match,
    dag,
    ulpin,
    parcel_geometry,
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {

        "metadata": {

            "analysis": (
                "Bhunaksha Dag 546 ↔ "
                "Overture Maps Buildings"
            ),

            "parcel_source": (
                "Assam Bhunaksha"
            ),

            "building_source": (
                "Overture Maps Buildings"
            ),

            "source_type": (
                "real_geospatial_data"
            ),

            "crs": TARGET_CRS,

            "dag": dag,

            "ulpin": ulpin,

            "parcel_geometry_type": (
                parcel_geometry.geom_type
            ),

            "parcel_area_m2": round(
                area(parcel_geometry),
                3,
            ),

            "strong_threshold_percent": (
                STRONG_THRESHOLD
            ),

            "partial_threshold_percent": (
                PARTIAL_THRESHOLD
            ),

            "nearby_threshold_m": (
                NEARBY_DISTANCE_M
            ),

            "legal_status": (
                "Spatial correspondence only; "
                "not proof of ownership."
            ),
        },

        "summary": {

            "total_buildings": len(
                results
            ),

            "strong_matches": len(
                strong
            ),

            "partial_matches": len(
                partial
            ),

            "nearby_buildings": len(
                nearby
            ),

            "no_matches": len(
                no_match
            ),

        },

        "results": results,

        "strong_matches": strong,

        "partial_matches": partial,

        "nearby_buildings": nearby,

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


# ================================================================
# MAIN
# ================================================================

def main():

    print("=" * 70)
    print("REAL DATA SPATIAL MATCH")
    print(
        "Bhunaksha Dag 546 ↔ Overture Buildings"
    )
    print("=" * 70)

    # ------------------------------------------------------------
    # Load
    # ------------------------------------------------------------

    (
        parcel_geometry,
        dag,
        ulpin,
    ) = load_parcel()

    buildings = load_overture()

    # ------------------------------------------------------------
    # Match
    # ------------------------------------------------------------

    (
        results,
        strong,
        partial,
        nearby,
        no_match,
    ) = match_buildings(
        buildings,
        parcel_geometry,
        dag,
        ulpin,
    )

    # ------------------------------------------------------------
    # Save
    # ------------------------------------------------------------

    output_file = save_results(
        results,
        strong,
        partial,
        nearby,
        no_match,
        dag,
        ulpin,
        parcel_geometry,
    )

    # ------------------------------------------------------------
    # Final report
    # ------------------------------------------------------------

    print()
    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

    print()
    print(
        "Results saved to:"
    )

    print(output_file)

    print()
    print(
        f"Strong matches:   {len(strong)}"
    )

    print(
        f"Partial matches:  {len(partial)}"
    )

    print(
        f"Nearby buildings: {len(nearby)}"
    )

    print(
        f"No matches:       {len(no_match)}"
    )

    print(
        f"Total buildings:  {len(results)}"
    )

    print()
    print("INTERPRETATION")
    print("-" * 70)

    if strong:
        print(
            "SUCCESS: Strong Overture building "
            "candidate(s) found inside Dag 546."
        )

    elif partial:
        print(
            "PARTIAL: Overture building geometry "
            "overlaps Dag 546."
        )

    elif nearby:
        print(
            "No building overlaps Dag 546, "
            "but nearby Overture buildings exist."
        )

    else:
        print(
            "No Overture building has a spatial "
            "relationship with Dag 546."
        )

    print()
    print(
        "IMPORTANT: Spatial overlap is not proof "
        "of legal ownership or cadastral authority."
    )


if __name__ == "__main__":
    main()