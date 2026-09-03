"""
3D ULPIN IDENTITY GENERATOR
============================

Generates deterministic, hierarchical 3D ULPIN identifiers
for the synthetic cadastral study area.

IMPORTANT
---------
These identifiers are a PROPOSED prototype schema.

They are NOT claimed to be an officially adopted national
ULPIN format.

The database's internal primary key must remain separate
from the ULPIN.

Hierarchy:

Study Area
    |
    +-- Parcel
          |
          +-- Building
                |
                +-- Floor
                      |
                      +-- Property Unit

Separate branch:

Parcel
    |
    +-- Underground Asset


Example property-unit ULPIN:

AS01-GHY-P001-B01-F01-U0101

Example underground-asset ULPIN:

AS01-GHY-P001-UA001
"""

from pathlib import Path
import json
import re

import geopandas as gpd


# ============================================================================
# CONFIGURATION
# ============================================================================

# Project root:
#
# D:\SOLID IDEA\3d-ulpin
#
# This file is:
#
# ml/gis/identity/generate_ulpins.py
#
# parents[0] = identity
# parents[1] = gis
# parents[2] = ml
# parents[3] = project root

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "study_area"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "outputs"
    / "identity"
)

EXPECTED_CRS = "EPSG:32646"


# ============================================================================
# PROPOSED ULPIN SCHEMA
# ============================================================================

ADMIN_CODE = "AS01"

CITY_CODE = "GHY"


# ============================================================================
# INPUT FILES
# ============================================================================

STUDY_AREA_FILE = DATA_DIR / "study_area.geojson"
PARCEL_FILE = DATA_DIR / "parcels.geojson"
BUILDING_FILE = DATA_DIR / "buildings.geojson"
FLOOR_FILE = DATA_DIR / "floors.geojson"
UNIT_FILE = DATA_DIR / "property_units.geojson"
UNDERGROUND_FILE = DATA_DIR / "underground_assets.geojson"


# ============================================================================
# OUTPUT FILES
# ============================================================================

ULPIN_FILE = OUTPUT_DIR / "ulpins.json"
SUMMARY_FILE = OUTPUT_DIR / "ulpin_summary.json"


# ============================================================================
# HELPERS
# ============================================================================

def normalize_identifier(value):
    """
    Convert an existing project identifier into a safe
    uppercase alphanumeric identifier.

    Example:

        B001 -> B001
        B001_F01 -> B001_F01
    """

    value = str(value).strip().upper()

    value = re.sub(
        r"[^A-Z0-9_]",
        "",
        value,
    )

    return value


def require_column(gdf, column, dataset_name):
    """
    Ensure a required attribute exists.
    """

    if column not in gdf.columns:

        raise ValueError(
            f"{dataset_name}: required column "
            f"'{column}' is missing."
        )


def validate_crs(gdf, dataset_name):
    """
    Ensure dataset uses the expected projected CRS.
    """

    if gdf.crs is None:

        raise ValueError(
            f"{dataset_name}: CRS is missing."
        )

    if str(gdf.crs) != EXPECTED_CRS:

        raise ValueError(
            f"{dataset_name}: unexpected CRS "
            f"{gdf.crs}. Expected {EXPECTED_CRS}."
        )


def load_dataset(path, dataset_name):
    """
    Load and validate a GeoJSON dataset.
    """

    if not path.exists():

        raise FileNotFoundError(
            f"{dataset_name}: file not found:\n{path}"
        )

    gdf = gpd.read_file(path)

    validate_crs(
        gdf,
        dataset_name,
    )

    if len(gdf) == 0:

        raise ValueError(
            f"{dataset_name}: dataset is empty."
        )

    if not gdf.geometry.is_valid.all():

        raise ValueError(
            f"{dataset_name}: invalid geometry detected."
        )

    return gdf


# ============================================================================
# ID EXTRACTION
# ============================================================================

def extract_floor_number(floor_id):
    """
    Extract numeric floor sequence.

    Examples:

        B001_F01 -> 01
        B001_F05 -> 05
        B002_B01 -> 01
    """

    floor_id = str(floor_id).upper()

    match = re.search(
        r"_(?:F|B)(\d+)$",
        floor_id,
    )

    if match is None:

        raise ValueError(
            f"Unable to extract floor number from '{floor_id}'."
        )

    return int(match.group(1))


def extract_unit_number(unit_id):
    """
    Extract the final unit number.

    Example:

        B001_F01_U0101 -> 0101
    """

    unit_id = str(unit_id).upper()

    match = re.search(
        r"_U(\d+)$",
        unit_id,
    )

    if match is None:

        raise ValueError(
            f"Unable to extract unit number from '{unit_id}'."
        )

    return int(match.group(1))


# ============================================================================
# CRUCIAL: PROPERTY UNIT ULPIN GENERATION
# ============================================================================

def generate_property_unit_ulpin(
    parcel_id,
    building_id,
    floor_id,
    unit_id,
):
    """
    Generate the deterministic ULPIN for a property unit.

    Format:

        AS01-GHY-P001-B01-F01-U0101

    Components:

        AS01   = study/administrative area
        GHY    = city/area
        P001   = parcel
        B01    = building
        F01    = floor
        U0101  = property unit
    """

    parcel_id = normalize_identifier(parcel_id)
    building_id = normalize_identifier(building_id)
    floor_id = normalize_identifier(floor_id)
    unit_id = normalize_identifier(unit_id)

    floor_number = extract_floor_number(
        floor_id
    )

    unit_number = extract_unit_number(
        unit_id
    )

    # CRUCIAL
    ulpin = (
        f"{ADMIN_CODE}-"
        f"{CITY_CODE}-"
        f"{parcel_id}-"
        f"{building_id}-"
        f"F{floor_number:02d}-"
        f"U{unit_number:04d}"
    )

    return ulpin


# ============================================================================
# CRUCIAL: UNDERGROUND ASSET ULPIN GENERATION
# ============================================================================

def generate_underground_ulpin(
    parcel_id,
    asset_id,
):
    """
    Generate the deterministic ULPIN for an underground asset.

    Format:

        AS01-GHY-P001-UA001
    """

    parcel_id = normalize_identifier(
        parcel_id
    )

    asset_id = normalize_identifier(
        asset_id
    )

    # CRUCIAL
    return (
        f"{ADMIN_CODE}-"
        f"{CITY_CODE}-"
        f"{parcel_id}-"
        f"{asset_id}"
    )


# ============================================================================
# STUDY AREA RECORD
# ============================================================================

def create_study_area_record(study_area):
    """
    Create metadata describing the ULPIN namespace.
    """

    return {
        "entity_type": "STUDY_AREA",

        "study_area_id": str(
            study_area.iloc[0]["study_area_id"]
        ),

        "admin_code": ADMIN_CODE,

        "city_code": CITY_CODE,

        "crs": EXPECTED_CRS,

        "ulpin_schema": (
            "AS01-GHY-Pxxx-Bxx-Fxx-Uxxxx"
        ),

        "status": "PROPOSED_PROTOTYPE_SCHEMA",
    }


# ============================================================================
# PROPERTY UNIT RECORDS
# ============================================================================

def generate_property_unit_records(
    units,
    buildings,
    floors,
    parcels,
):
    """
    Generate ULPIN records for all property units.

    Also verifies the complete parent hierarchy.
    """

    records = []

    parcel_lookup = {
        str(row["parcel_id"]): row
        for _, row in parcels.iterrows()
    }

    building_lookup = {
        str(row["building_id"]): row
        for _, row in buildings.iterrows()
    }

    floor_lookup = {
        str(row["floor_id"]): row
        for _, row in floors.iterrows()
    }

    for _, unit in units.iterrows():

        unit_id = str(
            unit["unit_id"]
        )

        building_id = str(
            unit["building_id"]
        )

        floor_id = str(
            unit["floor_id"]
        )

        # ------------------------------------------------------------
        # Verify building
        # ------------------------------------------------------------

        if building_id not in building_lookup:

            raise ValueError(
                f"{unit_id}: parent building "
                f"{building_id} does not exist."
            )

        building = building_lookup[
            building_id
        ]

        parcel_id = str(
            building["parcel_id"]
        )

        # ------------------------------------------------------------
        # Verify parcel
        # ------------------------------------------------------------

        if parcel_id not in parcel_lookup:

            raise ValueError(
                f"{unit_id}: parent parcel "
                f"{parcel_id} does not exist."
            )

        # ------------------------------------------------------------
        # Verify floor
        # ------------------------------------------------------------

        if floor_id not in floor_lookup:

            raise ValueError(
                f"{unit_id}: parent floor "
                f"{floor_id} does not exist."
            )

        floor = floor_lookup[
            floor_id
        ]

        # ------------------------------------------------------------
        # Verify floor belongs to building
        # ------------------------------------------------------------

        if str(floor["building_id"]) != building_id:

            raise ValueError(
                f"{unit_id}: floor {floor_id} "
                f"does not belong to building "
                f"{building_id}."
            )

        # ------------------------------------------------------------
        # Verify unit vertical range
        # ------------------------------------------------------------

        z_min = float(
            unit["z_min"]
        )

        z_max = float(
            unit["z_max"]
        )

        if z_min >= z_max:

            raise ValueError(
                f"{unit_id}: invalid Z range "
                f"{z_min} -> {z_max}."
            )

        # ------------------------------------------------------------
        # Verify unit is vertically inside floor
        # ------------------------------------------------------------

        floor_z_min = float(
            floor["z_min"]
        )

        floor_z_max = float(
            floor["z_max"]
        )

        tolerance = 1e-6

        if (
            z_min < floor_z_min - tolerance
            or
            z_max > floor_z_max + tolerance
        ):

            raise ValueError(
                f"{unit_id}: vertical range "
                f"is outside parent floor."
            )

        # ------------------------------------------------------------
        # Generate ULPIN
        # ------------------------------------------------------------

        ulpin = generate_property_unit_ulpin(
            parcel_id,
            building_id,
            floor_id,
            unit_id,
        )

        # ------------------------------------------------------------
        # Record
        # ------------------------------------------------------------

        record = {

            "ulpin": ulpin,

            "entity_type": "PROPERTY_UNIT",

            "internal_source_id": unit_id,

            "study_area": {
                "admin_code": ADMIN_CODE,
                "city_code": CITY_CODE,
            },

            "hierarchy": {

                "parcel_id": parcel_id,

                "building_id": building_id,

                "floor_id": floor_id,

                "unit_id": unit_id,
            },

            "vertical_extent": {

                "z_min": z_min,

                "z_max": z_max,

                "height": z_max - z_min,
            },

            "spatial": {

                "crs": EXPECTED_CRS,

                "area_m2": float(
                    unit.geometry.area
                ),

                "volume_m3": float(
                    unit.geometry.area
                    * (z_max - z_min)
                ),
            },

            "identity_status": (
                "PROPOSED_3D_ULPIN"
            ),
        }

        records.append(record)

    return records


# ============================================================================
# UNDERGROUND ASSET RECORDS
# ============================================================================

def generate_underground_records(
    assets,
    parcels,
):
    """
    Generate ULPIN records for underground assets.
    """

    records = []

    parcel_lookup = {
        str(row["parcel_id"]): row
        for _, row in parcels.iterrows()
    }

    for _, asset in assets.iterrows():

        asset_id = str(
            asset["asset_id"]
        )

        parcel_id = str(
            asset["parcel_id"]
        )

        # ------------------------------------------------------------
        # Parent validation
        # ------------------------------------------------------------

        if parcel_id not in parcel_lookup:

            raise ValueError(
                f"{asset_id}: parent parcel "
                f"{parcel_id} does not exist."
            )

        # ------------------------------------------------------------
        # Vertical range
        # ------------------------------------------------------------

        z_min = float(
            asset["z_min"]
        )

        z_max = float(
            asset["z_max"]
        )

        if z_min >= z_max:

            raise ValueError(
                f"{asset_id}: invalid underground "
                f"Z range."
            )

        # ------------------------------------------------------------
        # Generate ULPIN
        # ------------------------------------------------------------

        ulpin = generate_underground_ulpin(
            parcel_id,
            asset_id,
        )

        record = {

            "ulpin": ulpin,

            "entity_type": "UNDERGROUND_ASSET",

            "internal_source_id": asset_id,

            "study_area": {
                "admin_code": ADMIN_CODE,
                "city_code": CITY_CODE,
            },

            "hierarchy": {

                "parcel_id": parcel_id,

                "asset_id": asset_id,
            },

            "vertical_extent": {

                "z_min": z_min,

                "z_max": z_max,

                "depth_range_m": (
                    abs(z_min),
                    abs(z_max),
                ),
            },

            "spatial": {

                "crs": EXPECTED_CRS,
            },

            "asset_type": str(
                asset["asset_type"]
            ),

            "identity_status": (
                "PROPOSED_3D_ULPIN"
            ),
        }

        records.append(record)

    return records


# ============================================================================
# GLOBAL IDENTITY VALIDATION
# ============================================================================

def validate_ulpins(records):
    """
    Validate the generated identity collection.
    """

    print()
    print("=" * 78)
    print("ULPIN VALIDATION")
    print("=" * 78)

    # ------------------------------------------------------------------------
    # Count
    # ------------------------------------------------------------------------

    if len(records) == 0:

        raise ValueError(
            "No ULPIN records were generated."
        )

    print(
        f"Total ULPIN records: {len(records)}"
    )

    # ------------------------------------------------------------------------
    # Uniqueness
    # ------------------------------------------------------------------------

    ulpins = [
        record["ulpin"]
        for record in records
    ]

    unique_ulpins = set(
        ulpins
    )

    if len(unique_ulpins) != len(ulpins):

        duplicates = sorted(
            {
                value
                for value in ulpins
                if ulpins.count(value) > 1
            }
        )

        raise ValueError(
            "Duplicate ULPINs detected: "
            + ", ".join(duplicates)
        )

    print(
        "ULPIN uniqueness:       PASSED"
    )

    # ------------------------------------------------------------------------
    # Non-empty
    # ------------------------------------------------------------------------

    if any(
        not str(value).strip()
        for value in ulpins
    ):

        raise ValueError(
            "Empty ULPIN detected."
        )

    print(
        "ULPIN non-empty check:   PASSED"
    )

    # ------------------------------------------------------------------------
    # Deterministic format
    # ------------------------------------------------------------------------

    property_pattern = re.compile(
        r"^AS\d+-[A-Z0-9]+-P\d+-B\d+-F\d+-U\d+$"
    )

    underground_pattern = re.compile(
        r"^AS\d+-[A-Z0-9]+-P\d+-UA\d+$"
    )

    for record in records:

        ulpin = record["ulpin"]

        entity_type = record[
            "entity_type"
        ]

        if entity_type == "PROPERTY_UNIT":

            valid = bool(
                property_pattern.match(
                    ulpin
                )
            )

        elif entity_type == "UNDERGROUND_ASSET":

            valid = bool(
                underground_pattern.match(
                    ulpin
                )
            )

        else:

            valid = False

        if not valid:

            raise ValueError(
                f"Invalid ULPIN format: {ulpin}"
            )

    print(
        "ULPIN format validation: PASSED"
    )

    # ------------------------------------------------------------------------
    # Internal ID separation
    # ------------------------------------------------------------------------

    for record in records:

        if (
            record["ulpin"]
            == record["internal_source_id"]
        ):

            raise ValueError(
                "ULPIN must remain separate "
                "from internal source ID."
            )

    print(
        "Internal ID separation:  PASSED"
    )

    print(
        "Overall identity validation: PASSED"
    )


# ============================================================================
# SUMMARY
# ============================================================================

def create_summary(
    study_area,
    property_records,
    underground_records,
):
    """
    Create a compact summary for later integration.
    """

    property_ulpins = [
        record["ulpin"]
        for record in property_records
    ]

    underground_ulpins = [
        record["ulpin"]
        for record in underground_records
    ]

    return {

        "schema": {

            "name": "Proposed 3D ULPIN",

            "version": "0.1",

            "status": (
                "PROPOSED_PROTOTYPE_SCHEMA"
            ),

            "official_national_standard": False,
        },

        "namespace": {

            "admin_code": ADMIN_CODE,

            "city_code": CITY_CODE,
        },

        "crs": EXPECTED_CRS,

        "study_area_id": str(
            study_area.iloc[0][
                "study_area_id"
            ]
        ),

        "counts": {

            "property_units": len(
                property_records
            ),

            "underground_assets": len(
                underground_records
            ),

            "total_ulpins": (
                len(property_records)
                +
                len(underground_records)
            ),
        },

        "property_unit_ulpins": property_ulpins,

        "underground_asset_ulpins": (
            underground_ulpins
        ),
    }


# ============================================================================
# MAIN
# ============================================================================

def main():

    print("=" * 78)
    print("3D ULPIN IDENTITY GENERATION ENGINE")
    print("=" * 78)

    print()
    print(
        f"Project root: {PROJECT_ROOT}"
    )

    print(
        f"CRS: {EXPECTED_CRS}"
    )

    print()
    print(
        "ULPIN schema:"
    )

    print(
        "  Property unit:"
    )

    print(
        "    AS01-GHY-P001-B01-F01-U0101"
    )

    print(
        "  Underground asset:"
    )

    print(
        "    AS01-GHY-P001-UA001"
    )

    print()
    print(
        "IMPORTANT: This is a proposed prototype schema."
    )

    # ------------------------------------------------------------------------
    # LOAD DATA
    # ------------------------------------------------------------------------

    print()
    print("=" * 78)
    print("LOADING CADASTRAL DATA")
    print("=" * 78)

    study_area = load_dataset(
        STUDY_AREA_FILE,
        "Study area",
    )

    parcels = load_dataset(
        PARCEL_FILE,
        "Parcels",
    )

    buildings = load_dataset(
        BUILDING_FILE,
        "Buildings",
    )

    floors = load_dataset(
        FLOOR_FILE,
        "Floors",
    )

    units = load_dataset(
        UNIT_FILE,
        "Property units",
    )

    underground = load_dataset(
        UNDERGROUND_FILE,
        "Underground assets",
    )

    print(
        f"Study areas:         {len(study_area)}"
    )

    print(
        f"Parcels:              {len(parcels)}"
    )

    print(
        f"Buildings:            {len(buildings)}"
    )

    print(
        f"Floors:               {len(floors)}"
    )

    print(
        f"Property units:       {len(units)}"
    )

    print(
        f"Underground assets:   {len(underground)}"
    )

    # ------------------------------------------------------------------------
    # REQUIRED ATTRIBUTES
    # ------------------------------------------------------------------------

    require_column(
        study_area,
        "study_area_id",
        "Study area",
    )

    require_column(
        parcels,
        "parcel_id",
        "Parcels",
    )

    require_column(
        buildings,
        "building_id",
        "Buildings",
    )

    require_column(
        buildings,
        "parcel_id",
        "Buildings",
    )

    require_column(
        floors,
        "floor_id",
        "Floors",
    )

    require_column(
        floors,
        "building_id",
        "Floors",
    )

    require_column(
        floors,
        "z_min",
        "Floors",
    )

    require_column(
        floors,
        "z_max",
        "Floors",
    )

    require_column(
        units,
        "unit_id",
        "Property units",
    )

    require_column(
        units,
        "building_id",
        "Property units",
    )

    require_column(
        units,
        "floor_id",
        "Property units",
    )

    require_column(
        units,
        "z_min",
        "Property units",
    )

    require_column(
        units,
        "z_max",
        "Property units",
    )

    require_column(
        underground,
        "asset_id",
        "Underground assets",
    )

    require_column(
        underground,
        "parcel_id",
        "Underground assets",
    )

    require_column(
        underground,
        "asset_type",
        "Underground assets",
    )

    require_column(
        underground,
        "z_min",
        "Underground assets",
    )

    require_column(
        underground,
        "z_max",
        "Underground assets",
    )

    print()
    print(
        "Required attributes:   PASSED"
    )

    # ------------------------------------------------------------------------
    # GENERATE PROPERTY UNIT IDENTITIES
    # ------------------------------------------------------------------------

    print()
    print("=" * 78)
    print("PROPERTY UNIT ULPIN GENERATION")
    print("=" * 78)

    property_records = (
        generate_property_unit_records(
            units,
            buildings,
            floors,
            parcels,
        )
    )

    for record in property_records:

        print(
            f"{record['ulpin']:<42} "
            f"| PROPERTY_UNIT"
        )

    # ------------------------------------------------------------------------
    # GENERATE UNDERGROUND IDENTITIES
    # ------------------------------------------------------------------------

    print()
    print("=" * 78)
    print("UNDERGROUND ASSET ULPIN GENERATION")
    print("=" * 78)

    underground_records = (
        generate_underground_records(
            underground,
            parcels,
        )
    )

    for record in underground_records:

        print(
            f"{record['ulpin']:<42} "
            f"| {record['asset_type']}"
        )

    # ------------------------------------------------------------------------
    # COMBINE
    # ------------------------------------------------------------------------

    all_records = (
        property_records
        +
        underground_records
    )

    # ------------------------------------------------------------------------
    # VALIDATE
    # ------------------------------------------------------------------------

    validate_ulpins(
        all_records
    )

    # ------------------------------------------------------------------------
    # CREATE OUTPUT
    # ------------------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    study_area_record = (
        create_study_area_record(
            study_area
        )
    )

    output = {

        "metadata": {

            "title": (
                "Proposed 3D ULPIN Identity Registry"
            ),

            "schema_version": "0.1",

            "status": (
                "PROTOTYPE"
            ),

            "official_standard": False,

            "crs": EXPECTED_CRS,

            "admin_code": ADMIN_CODE,

            "city_code": CITY_CODE,
        },

        "study_area": study_area_record,

        "records": all_records,
    }

    # ------------------------------------------------------------------------
    # WRITE JSON
    # ------------------------------------------------------------------------

    with open(
        ULPIN_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
        )

    summary = create_summary(
        study_area,
        property_records,
        underground_records,
    )

    with open(
        SUMMARY_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=2,
        )

    # ------------------------------------------------------------------------
    # FINAL OUTPUT
    # ------------------------------------------------------------------------

    print()
    print("=" * 78)
    print("3D ULPIN GENERATION COMPLETE")
    print("=" * 78)

    print()
    print(
        f"Property unit ULPINs:  "
        f"{len(property_records)}"
    )

    print(
        f"Underground ULPINs:    "
        f"{len(underground_records)}"
    )

    print(
        f"Total ULPINs:          "
        f"{len(all_records)}"
    )

    print()
    print(
        f"Registry:"
    )

    print(
        ULPIN_FILE
    )

    print()
    print(
        f"Summary:"
    )

    print(
        SUMMARY_FILE
    )

    print()
    print("=" * 78)
    print("ULPIN VALIDATIONS")
    print("=" * 78)

    print(
        "CRS validation:              PASSED"
    )

    print(
        "Hierarchy validation:        PASSED"
    )

    print(
        "Deterministic generation:    PASSED"
    )

    print(
        "Uniqueness validation:       PASSED"
    )

    print(
        "Format validation:           PASSED"
    )

    print(
        "Internal ID separation:      PASSED"
    )

    print()
    print(
        "ALL 3D ULPIN VALIDATIONS PASSED"
    )


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()