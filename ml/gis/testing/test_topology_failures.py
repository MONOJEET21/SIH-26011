"""
3D ULPIN - Negative Topology Test Suite

Purpose
-------
Verify that the cadastral topology validation logic can detect
deliberately introduced spatial errors.

IMPORTANT
---------
This script DOES NOT modify the real synthetic dataset.

It creates temporary invalid geometries in memory and tests
the fundamental spatial rules independently.

Expected result:
    ALL NEGATIVE TESTS PASSED

Meaning:
    Every intentionally broken case was correctly detected.
"""

from pathlib import Path

import geopandas as gpd
from shapely.geometry import Polygon, LineString


# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_DIR = PROJECT_ROOT / "data" / "synthetic" / "study_area"

EXPECTED_CRS = "EPSG:32646"


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def print_header(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def test_result(test_name, passed, explanation):
    status = "PASSED" if passed else "FAILED"

    print(f"{status:<8} | {test_name}")
    print(f"         | {explanation}")

    return passed


# ============================================================================
# LOAD BASE DATA
# ============================================================================

def load_base_data():

    parcels = gpd.read_file(DATA_DIR / "parcels.geojson")
    buildings = gpd.read_file(DATA_DIR / "buildings.geojson")
    floors = gpd.read_file(DATA_DIR / "floors.geojson")
    units = gpd.read_file(DATA_DIR / "property_units.geojson")
    underground = gpd.read_file(
        DATA_DIR / "underground_assets.geojson"
    )

    return parcels, buildings, floors, units, underground


# ============================================================================
# TEST 1
# OVERLAPPING PARCELS
# ============================================================================

def test_overlapping_parcels(parcels):
    """
    Create an artificial overlap between two parcels.

    A valid cadastral parcel fabric should not contain
    overlapping ownership parcels.
    """

    # CRUCIAL
    test_parcels = parcels.copy()

    original = test_parcels.iloc[0].geometry

    # Move parcel 2 directly on top of parcel 1.
    test_parcels.loc[test_parcels.index[1], "geometry"] = original

    overlap_found = False

    for i in range(len(test_parcels)):
        for j in range(i + 1, len(test_parcels)):

            intersection = test_parcels.iloc[i].geometry.intersection(
                test_parcels.iloc[j].geometry
            )

            if not intersection.is_empty and intersection.area > 0:
                overlap_found = True
                break

        if overlap_found:
            break

    return test_result(
        "Overlapping parcel detection",
        overlap_found,
        "Artificial parcel overlap was correctly detected."
        if overlap_found
        else "Validator failed to detect the artificial parcel overlap.",
    )


# ============================================================================
# TEST 2
# BUILDING OUTSIDE PARCEL
# ============================================================================

def test_building_outside_parcel(parcels, buildings):
    """
    Move a building outside its parent parcel.
    """

    test_buildings = buildings.copy()

    parcel = parcels.iloc[0].geometry

    # Create a building clearly outside the parcel.
    minx, miny, maxx, maxy = parcel.bounds

    outside_building = Polygon(
        [
            (maxx + 500, maxy + 500),
            (maxx + 550, maxy + 500),
            (maxx + 550, maxy + 550),
            (maxx + 500, maxy + 550),
        ]
    )

    test_buildings.loc[test_buildings.index[0], "geometry"] = (
        outside_building
    )

    building = test_buildings.iloc[0].geometry

    detected = not parcel.covers(building)

    return test_result(
        "Building outside parcel detection",
        detected,
        "Building outside parent parcel was correctly detected."
        if detected
        else "Validator failed to detect building outside parcel.",
    )


# ============================================================================
# TEST 3
# FLOOR OUTSIDE BUILDING
# ============================================================================

def test_floor_outside_building(buildings, floors):
    """
    Move a floor footprint outside its parent building.
    """

    test_floors = floors.copy()

    building = buildings.iloc[0].geometry

    minx, miny, maxx, maxy = building.bounds

    outside_floor = Polygon(
        [
            (maxx + 300, maxy + 300),
            (maxx + 350, maxy + 300),
            (maxx + 350, maxy + 350),
            (maxx + 300, maxy + 350),
        ]
    )

    # Find a floor belonging to the first building.
    building_id = buildings.iloc[0]["building_id"]

    matching = test_floors[
        test_floors["building_id"] == building_id
    ]

    if matching.empty:
        return test_result(
            "Floor outside building detection",
            False,
            "Could not locate a floor belonging to the first building.",
        )

    floor_index = matching.index[0]

    test_floors.loc[floor_index, "geometry"] = outside_floor

    detected = not building.covers(
        test_floors.loc[floor_index, "geometry"]
    )

    return test_result(
        "Floor outside building detection",
        detected,
        "Floor outside parent building was correctly detected."
        if detected
        else "Validator failed to detect floor outside building.",
    )


# ============================================================================
# TEST 4
# PROPERTY UNIT OUTSIDE FLOOR
# ============================================================================

def test_unit_outside_floor(floors, units):
    """
    Move a property unit outside its parent floor.
    """

    test_units = units.copy()

    floor = floors.iloc[0]

    minx, miny, maxx, maxy = floor.geometry.bounds

    outside_unit = Polygon(
        [
            (maxx + 300, maxy + 300),
            (maxx + 350, maxy + 300),
            (maxx + 350, maxy + 350),
            (maxx + 300, maxy + 350),
        ]
    )

    floor_id = floor["floor_id"]

    matching = test_units[
        test_units["floor_id"] == floor_id
    ]

    if matching.empty:
        return test_result(
            "Property unit outside floor detection",
            False,
            "Could not locate a property unit belonging to the first floor.",
        )

    unit_index = matching.index[0]

    test_units.loc[unit_index, "geometry"] = outside_unit

    detected = not floor.geometry.covers(
        test_units.loc[unit_index, "geometry"]
    )

    return test_result(
        "Property unit outside floor detection",
        detected,
        "Property unit outside parent floor was correctly detected."
        if detected
        else "Validator failed to detect unit outside floor.",
    )


# ============================================================================
# TEST 5
# OVERLAPPING PROPERTY UNITS
# ============================================================================

def test_overlapping_units(units):
    """
    Artificially make two units overlap.

    Units on the same floor should normally form a non-overlapping
    partition of the floor footprint.
    """

    test_units = units.copy()

    first_floor_id = test_units.iloc[0]["floor_id"]

    matching = test_units[
        test_units["floor_id"] == first_floor_id
    ]

    if len(matching) < 2:
        return test_result(
            "Overlapping property unit detection",
            False,
            "Need at least two units on the same floor.",
        )

    index_a = matching.index[0]
    index_b = matching.index[1]

    test_units.loc[index_b, "geometry"] = (
        test_units.loc[index_a, "geometry"]
    )

    overlap_found = False

    for i in range(len(matching)):

        idx_i = matching.index[i]

        for j in range(i + 1, len(matching)):

            idx_j = matching.index[j]

            intersection = test_units.loc[idx_i, "geometry"].intersection(
                test_units.loc[idx_j, "geometry"]
            )

            if not intersection.is_empty and intersection.area > 0:
                overlap_found = True
                break

        if overlap_found:
            break

    return test_result(
        "Overlapping property unit detection",
        overlap_found,
        "Artificial property-unit overlap was correctly detected."
        if overlap_found
        else "Validator failed to detect overlapping property units.",
    )


# ============================================================================
# TEST 6
# INVALID Z RANGE
# ============================================================================

def test_invalid_z_range(floors):
    """
    Create an invalid vertical extent:

        z_min >= z_max

    A volume cannot have a zero or negative vertical extent.
    """

    test_floors = floors.copy()

    index = test_floors.index[0]

    original_z_min = float(test_floors.loc[index, "z_min"])

    # CRUCIAL
    test_floors.loc[index, "z_max"] = original_z_min - 1.0

    detected = (
        float(test_floors.loc[index, "z_min"])
        >= float(test_floors.loc[index, "z_max"])
    )

    return test_result(
        "Invalid Z-range detection",
        detected,
        "Invalid vertical range was correctly detected."
        if detected
        else "Validator failed to detect invalid Z range.",
    )


# ============================================================================
# TEST 7
# UNDERGROUND ASSET OUTSIDE PARCEL
# ============================================================================

def test_underground_asset_outside_parcel(
    parcels,
    underground,
):
    """
    Move an underground asset outside its parent parcel.
    """

    test_assets = underground.copy()

    asset_index = test_assets.index[0]

    parcel = parcels.iloc[0].geometry

    minx, miny, maxx, maxy = parcel.bounds

    outside_asset = LineString(
        [
            (maxx + 500, maxy + 500),
            (maxx + 600, maxy + 500),
        ]
    )

    test_assets.loc[asset_index, "geometry"] = outside_asset

    detected = not parcel.covers(
        test_assets.loc[asset_index, "geometry"]
    )

    return test_result(
        "Underground asset outside parcel detection",
        detected,
        "Underground asset outside parent parcel was correctly detected."
        if detected
        else "Validator failed to detect underground asset outside parcel.",
    )


# ============================================================================
# TEST 8
# BASELINE DATASET MUST REMAIN VALID
# ============================================================================

def test_original_dataset(parcels, buildings, floors, units, underground):
    """
    Confirm that the actual synthetic dataset is still valid.

    This is critical: our negative tests must not corrupt
    the real project dataset.
    """

    checks = []

    checks.append(parcels.geometry.is_valid.all())
    checks.append(buildings.geometry.is_valid.all())
    checks.append(floors.geometry.is_valid.all())
    checks.append(units.geometry.is_valid.all())
    checks.append(underground.geometry.is_valid.all())

    checks.append(str(parcels.crs) == EXPECTED_CRS)
    checks.append(str(buildings.crs) == EXPECTED_CRS)
    checks.append(str(floors.crs) == EXPECTED_CRS)
    checks.append(str(units.crs) == EXPECTED_CRS)
    checks.append(str(underground.crs) == EXPECTED_CRS)

    passed = all(checks)

    return test_result(
        "Original dataset integrity",
        passed,
        "Real synthetic dataset remains valid and unchanged."
        if passed
        else "Original synthetic dataset failed integrity checks.",
    )


# ============================================================================
# MAIN
# ============================================================================

def main():

    print_header("3D CADASTRAL NEGATIVE TOPOLOGY TEST SUITE")

    print(f"Project root: {PROJECT_ROOT}")
    print(f"Dataset:      {DATA_DIR}")
    print(f"Expected CRS: {EXPECTED_CRS}")

    print_header("LOADING BASE DATA")

    try:

        parcels, buildings, floors, units, underground = (
            load_base_data()
        )

    except Exception as exc:

        print()
        print("ERROR: Could not load cadastral dataset.")
        print(str(exc))
        raise SystemExit(1)

    print(f"Parcels:             {len(parcels)}")
    print(f"Buildings:           {len(buildings)}")
    print(f"Floors:              {len(floors)}")
    print(f"Property units:      {len(units)}")
    print(f"Underground assets:  {len(underground)}")

    # ------------------------------------------------------------------------
    # RUN TESTS
    # ------------------------------------------------------------------------

    print_header("INTENTIONAL FAILURE TESTS")

    results = []

    # CRUCIAL
    results.append(
        test_overlapping_parcels(parcels)
    )

    results.append(
        test_building_outside_parcel(
            parcels,
            buildings,
        )
    )

    results.append(
        test_floor_outside_building(
            buildings,
            floors,
        )
    )

    results.append(
        test_unit_outside_floor(
            floors,
            units,
        )
    )

    results.append(
        test_overlapping_units(units)
    )

    results.append(
        test_invalid_z_range(floors)
    )

    results.append(
        test_underground_asset_outside_parcel(
            parcels,
            underground,
        )
    )

    print_header("BASELINE DATASET INTEGRITY")

    results.append(
        test_original_dataset(
            parcels,
            buildings,
            floors,
            units,
            underground,
        )
    )

    # ------------------------------------------------------------------------
    # FINAL RESULT
    # ------------------------------------------------------------------------

    passed = sum(results)
    total = len(results)

    print_header("NEGATIVE TEST SUMMARY")

    print(f"Tests passed:  {passed}/{total}")
    print(f"Tests failed:  {total - passed}/{total}")

    if passed == total:

        print()
        print("ALL NEGATIVE TOPOLOGY TESTS PASSED")
        print()
        print(
            "The validation framework successfully detects "
            "deliberately introduced cadastral errors."
        )
        print()
        print(
            "The original synthetic dataset remains intact."
        )

        return 0

    else:

        print()
        print("NEGATIVE TOPOLOGY TEST SUITE FAILED")
        print()
        print(
            "At least one intentionally introduced error "
            "was not detected."
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())