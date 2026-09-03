from pathlib import Path
import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

PARCEL_FILE = (
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

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "real"
    / "analysis"
    / "dag_546_overture_candidates.geojson"
)

TARGET_CRS = "EPSG:4326"


def main():

    print("=" * 70)
    print("DAG 546 — OVERTURE BUILDING CANDIDATES")
    print("=" * 70)

    parcel = gpd.read_file(PARCEL_FILE)
    buildings = gpd.read_file(OVERTURE_FILE)

    if parcel.crs is None:
        parcel = parcel.set_crs("EPSG:32646")

    if buildings.crs is None:
        buildings = buildings.set_crs("EPSG:4326")

    # Work in metric CRS
    parcel = parcel.to_crs("EPSG:32646")
    buildings = buildings.to_crs("EPSG:32646")

    parcel_geometry = parcel.geometry.iloc[0]

    output_features = []

    # --------------------------------------------------------------
    # Parcel
    # --------------------------------------------------------------

    parcel_row = parcel.iloc[0].copy()

    parcel_row["feature_type"] = "parcel"
    parcel_row["feature_id"] = "DAG_546"
    parcel_row["ulpin"] = "8456A2E5NVP0H0"
    parcel_row["match_class"] = "authoritative_parcel"

    output_features.append(
        parcel_row
    )

    # --------------------------------------------------------------
    # Buildings
    # --------------------------------------------------------------

    for index, row in buildings.iterrows():

        geometry = row.geometry

        if geometry is None or geometry.is_empty:
            continue

        building_id = str(
            row.get("id")
            or f"overture_{index}"
        )

        building_area = geometry.area

        intersection = geometry.intersection(
            parcel_geometry
        )

        intersection_area = intersection.area

        percent_inside = (
            intersection_area
            / building_area
            * 100
            if building_area > 0
            else 0
        )

        if percent_inside >= 50:
            match_class = "strong_match"
        elif percent_inside > 0:
            match_class = "partial_match"
        else:
            distance = geometry.distance(
                parcel_geometry
            )

            if distance <= 100:
                match_class = "nearby"
            else:
                match_class = "outside"

        new_row = row.copy()

        new_row["feature_type"] = "building"
        new_row["feature_id"] = building_id
        new_row["ulpin"] = "8456A2E5NVP0H0"
        new_row["parcel_id"] = "DAG_546"

        new_row["building_area_m2"] = round(
            building_area,
            3,
        )

        new_row["intersection_area_m2"] = round(
            intersection_area,
            3,
        )

        new_row["percent_inside_parcel"] = round(
            percent_inside,
            3,
        )

        new_row["match_class"] = match_class

        output_features.append(
            new_row
        )

    # --------------------------------------------------------------
    # Create GeoDataFrame
    # --------------------------------------------------------------

    result = gpd.GeoDataFrame(
        output_features,
        geometry="geometry",
        crs="EPSG:32646",
    )

    result = result.to_crs(
        TARGET_CRS
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_file(
        OUTPUT_FILE,
        driver="GeoJSON",
    )

    print()
    print("Saved:")
    print(OUTPUT_FILE)

    print()
    print("Features:")
    print(len(result))

    print()
    print(
        result[
            [
                "feature_type",
                "feature_id",
                "match_class",
            ]
        ].to_string(index=False)
    )

    print()
    print("Done.")


if __name__ == "__main__":
    main()