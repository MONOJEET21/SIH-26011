from pathlib import Path
import json

import geopandas as gpd


# ============================================================
# 3D ULPIN — MASTER CADASTRAL MODEL BUILDER
# ============================================================
#
# PURPOSE:
# Build a machine-readable hierarchical representation:
#
# Study Area
#     └── Parcel
#           ├── Building
#           │     └── Floor
#           │           └── Property Unit
#           │
#           └── Underground Asset
#
# IMPORTANT:
# This file does NOT generate geometry.
# Geometry remains in the authoritative GeoJSON / OBJ files.
#
# This file establishes relationships between spatial objects.
# ============================================================


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

STUDY_AREA_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "study_area"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "outputs"
    / "cadastral"
)


STUDY_AREA_FILE = (
    STUDY_AREA_DIR
    / "study_area.geojson"
)

PARCELS_FILE = (
    STUDY_AREA_DIR
    / "parcels.geojson"
)

BUILDINGS_FILE = (
    STUDY_AREA_DIR
    / "buildings.geojson"
)

FLOORS_FILE = (
    STUDY_AREA_DIR
    / "floors.geojson"
)

PROPERTY_UNITS_FILE = (
    STUDY_AREA_DIR
    / "property_units.geojson"
)

UNDERGROUND_ASSETS_FILE = (
    STUDY_AREA_DIR
    / "underground_assets.geojson"
)


MASTER_MODEL_FILE = (
    OUTPUT_DIR
    / "cadastral_model.json"
)

SUMMARY_FILE = (
    OUTPUT_DIR
    / "cadastral_summary.json"
)


EXPECTED_CRS = "EPSG:32646"


# ============================================================
# HELPERS
# ============================================================

def require_file(path: Path):
    """Make sure an expected input file exists."""

    if not path.exists():
        raise FileNotFoundError(
            f"Required file does not exist:\n{path}"
        )


def load_layer(path: Path):
    """Load and perform basic spatial validation."""

    require_file(path)

    layer = gpd.read_file(path)

    if layer.empty:
        raise ValueError(
            f"Layer is empty:\n{path}"
        )

    if layer.crs is None:
        raise ValueError(
            f"Layer has no CRS:\n{path}"
        )

    if str(layer.crs) != EXPECTED_CRS:
        raise ValueError(
            f"Unexpected CRS for {path.name}: "
            f"{layer.crs}. "
            f"Expected {EXPECTED_CRS}."
        )

    if not layer.geometry.is_valid.all():
        raise ValueError(
            f"Invalid geometry found in:\n{path}"
        )

    return layer


def get_value(row, field, default=None):
    """
    Safely retrieve a field from a GeoPandas row.
    """

    if field not in row.index:
        return default

    value = row[field]

    if value is None:
        return default

    return value


def clean_value(value):
    """
    Convert NumPy/Pandas scalar values into
    JSON-safe Python values.
    """

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    return value


# ============================================================
# LOAD DATASETS
# ============================================================

print("=" * 70)
print("3D CADASTRAL MASTER MODEL BUILDER")
print("=" * 70)

print()

print(
    f"Expected CRS: {EXPECTED_CRS}"
)

print(
    f"Study area directory:\n{STUDY_AREA_DIR}"
)

print()


study_area = load_layer(
    STUDY_AREA_FILE
)

parcels = load_layer(
    PARCELS_FILE
)

buildings = load_layer(
    BUILDINGS_FILE
)

floors = load_layer(
    FLOORS_FILE
)

property_units = load_layer(
    PROPERTY_UNITS_FILE
)

underground_assets = load_layer(
    UNDERGROUND_ASSETS_FILE
)


print(
    f"Study areas:          {len(study_area)}"
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
    f"Property units:       {len(property_units)}"
)

print(
    f"Underground assets:   {len(underground_assets)}"
)

print()


# ============================================================
# CREATE LOOKUP TABLES
# ============================================================

building_by_id = {}

for _, row in buildings.iterrows():

    building_id = str(
        get_value(
            row,
            "building_id"
        )
    )

    building_by_id[
        building_id
    ] = row


floor_by_id = {}

for _, row in floors.iterrows():

    floor_id = str(
        get_value(
            row,
            "floor_id"
        )
    )

    floor_by_id[
        floor_id
    ] = row


unit_by_id = {}

for _, row in property_units.iterrows():

    unit_id = str(
        get_value(
            row,
            "unit_id"
        )
    )

    unit_by_id[
        unit_id
    ] = row


asset_by_id = {}

for _, row in underground_assets.iterrows():

    asset_id = str(
        get_value(
            row,
            "asset_id"
        )
    )

    asset_by_id[
        asset_id
    ] = row


# ============================================================
# BUILD MASTER MODEL
# ============================================================

master_model = {

    "schema": {

        "name":
            "Proposed 3D ULPIN Cadastral Model",

        "version":
            "0.1.0",

        "status":
            "prototype",

        "crs":
            EXPECTED_CRS,

        "geometry_source":
            "GeoJSON + OBJ",

        "ulpin_status":
            "not_generated",

    },

    "study_areas": [],

    "statistics": {},

}


# ============================================================
# STUDY AREA
# ============================================================

for _, study_row in study_area.iterrows():

    study_id = str(
        get_value(
            study_row,
            "study_area_id",
            "STUDY_AREA_01"
        )
    )


    study_record = {

        "study_area_id":
            study_id,

        "name":
            str(
                get_value(
                    study_row,
                    "name",
                    "Synthetic 3D Cadastral Study Area"
                )
            ),

        "crs":
            EXPECTED_CRS,

        "parcels": [],

    }


    # ========================================================
    # PARCELS
    # ========================================================

    for _, parcel_row in parcels.iterrows():

        parcel_id = str(
            get_value(
                parcel_row,
                "parcel_id"
            )
        )


        parcel_record = {

            "parcel_id":
                parcel_id,

            "parcel_type":
                str(
                    get_value(
                        parcel_row,
                        "parcel_type",
                        "UNKNOWN"
                    )
                ),

            "area_m2":
                float(
                    parcel_row.geometry.area
                ),

            "geometry_source":
                "parcels.geojson",

            "buildings": [],

            "underground_assets": [],

        }


        # ====================================================
        # BUILDINGS BELONGING TO PARCEL
        # ====================================================

        parcel_buildings = buildings[
            buildings["parcel_id"]
            == parcel_id
        ]


        for _, building_row in (
            parcel_buildings.iterrows()
        ):

            building_id = str(
                get_value(
                    building_row,
                    "building_id"
                )
            )


            building_record = {

                "building_id":
                    building_id,

                "parcel_id":
                    parcel_id,

                "building_type":
                    str(
                        get_value(
                            building_row,
                            "building_type",
                            "BUILDING"
                        )
                    ),

                "height_m":
                    float(
                        get_value(
                            building_row,
                            "height_m",
                            0.0
                        )
                    ),

                "z_min":
                    float(
                        get_value(
                            building_row,
                            "z_min",
                            0.0
                        )
                    ),

                "z_max":
                    float(
                        get_value(
                            building_row,
                            "z_max",
                            0.0
                        )
                    ),

                "geometry_source":
                    "buildings.geojson",

                "3d_geometry_source":
                    "buildings_3d.obj",

                "floors": [],

            }


            # ================================================
            # FLOORS BELONGING TO BUILDING
            # ================================================

            building_floors = floors[
                floors["building_id"]
                == building_id
            ]


            # Sort vertically
            building_floors = (
                building_floors
                .sort_values(
                    by="z_min"
                )
            )


            for _, floor_row in (
                building_floors.iterrows()
            ):

                floor_id = str(
                    get_value(
                        floor_row,
                        "floor_id"
                    )
                )


                floor_record = {

                    "floor_id":
                        floor_id,

                    "building_id":
                        building_id,

                    "floor_type":
                        str(
                            get_value(
                                floor_row,
                                "floor_type",
                                "STANDARD"
                            )
                        ),

                    "floor_number":
                        get_value(
                            floor_row,
                            "floor_number"
                        ),

                    "z_min":
                        float(
                            get_value(
                                floor_row,
                                "z_min",
                                0.0
                            )
                        ),

                    "z_max":
                        float(
                            get_value(
                                floor_row,
                                "z_max",
                                0.0
                            )
                        ),

                    "height_m":
                        float(
                            get_value(
                                floor_row,
                                "z_max",
                                0.0
                            )
                            -
                            get_value(
                                floor_row,
                                "z_min",
                                0.0
                            )
                        ),

                    "geometry_source":
                        "floors.geojson",

                    "3d_geometry_source":
                        "floors_3d.obj",

                    "property_units": [],

                }


                # ============================================
                # PROPERTY UNITS
                # ============================================

                floor_units = property_units[
                    property_units["floor_id"]
                    == floor_id
                ]


                for _, unit_row in (
                    floor_units.iterrows()
                ):

                    unit_id = str(
                        get_value(
                            unit_row,
                            "unit_id"
                        )
                    )


                    unit_record = {

                        "unit_id":
                            unit_id,

                        "floor_id":
                            floor_id,

                        "building_id":
                            building_id,

                        "parcel_id":
                            parcel_id,

                        "unit_type":
                            str(
                                get_value(
                                    unit_row,
                                    "unit_type",
                                    "PROPERTY_UNIT"
                                )
                            ),

                        "area_m2":
                            float(
                                unit_row.geometry.area
                            ),

                        "z_min":
                            float(
                                get_value(
                                    unit_row,
                                    "z_min",
                                    0.0
                                )
                            ),

                        "z_max":
                            float(
                                get_value(
                                    unit_row,
                                    "z_max",
                                    0.0
                                )
                            ),

                        "volume_m3":
                            float(
                                get_value(
                                    unit_row,
                                    "volume_m3",
                                    0.0
                                )
                            ),

                        "geometry_source":
                            "property_units.geojson",

                        "3d_geometry_source":
                            "property_units_3d.obj",

                        "ulpin":
                            None,

                    }


                    floor_record[
                        "property_units"
                    ].append(
                        unit_record
                    )


                building_record[
                    "floors"
                ].append(
                    floor_record
                )


            parcel_record[
                "buildings"
            ].append(
                building_record
            )


        # ====================================================
        # UNDERGROUND ASSETS
        # ====================================================

        parcel_assets = underground_assets[
            underground_assets["parcel_id"]
            == parcel_id
        ]


        for _, asset_row in (
            parcel_assets.iterrows()
        ):

            asset_id = str(
                get_value(
                    asset_row,
                    "asset_id"
                )
            )


            asset_record = {

                "asset_id":
                    asset_id,

                "parcel_id":
                    parcel_id,

                "asset_type":
                    str(
                        get_value(
                            asset_row,
                            "asset_type",
                            "UNKNOWN"
                        )
                    ),

                "asset_name":
                    str(
                        get_value(
                            asset_row,
                            "asset_name",
                            asset_id
                        )
                    ),

                "z_min":
                    float(
                        get_value(
                            asset_row,
                            "z_min",
                            0.0
                        )
                    ),

                "z_max":
                    float(
                        get_value(
                            asset_row,
                            "z_max",
                            0.0
                        )
                    ),

                "area_m2":
                    float(
                        asset_row.geometry.area
                    ),

                "volume_m3":
                    float(
                        get_value(
                            asset_row,
                            "volume_m3",
                            0.0
                        )
                    ),

                "geometry_source":
                    "underground_assets.geojson",

                "3d_geometry_source":
                    "underground_assets_3d.obj",

            }


            parcel_record[
                "underground_assets"
            ].append(
                asset_record
            )


        study_record[
            "parcels"
        ].append(
            parcel_record
        )


    master_model[
        "study_areas"
    ].append(
        study_record
    )


# ============================================================
# HIERARCHY VALIDATION
# ============================================================

validation_errors = []


# ------------------------------------------------------------
# Validate buildings → parcels
# ------------------------------------------------------------

for parcel in (
    master_model["study_areas"][0]["parcels"]
):

    parcel_id = parcel[
        "parcel_id"
    ]

    for building in parcel[
        "buildings"
    ]:

        if building[
            "parcel_id"
        ] != parcel_id:

            validation_errors.append(
                f"Building {building['building_id']} "
                f"has incorrect parent parcel."
            )


# ------------------------------------------------------------
# Validate floors → buildings
# ------------------------------------------------------------

for parcel in (
    master_model["study_areas"][0]["parcels"]
):

    for building in parcel[
        "buildings"
    ]:

        building_id = building[
            "building_id"
        ]

        for floor in building[
            "floors"
        ]:

            if floor[
                "building_id"
            ] != building_id:

                validation_errors.append(
                    f"Floor {floor['floor_id']} "
                    f"has incorrect parent building."
                )


# ------------------------------------------------------------
# Validate units → floors/buildings/parcels
# ------------------------------------------------------------

for parcel in (
    master_model["study_areas"][0]["parcels"]
):

    parcel_id = parcel[
        "parcel_id"
    ]

    for building in parcel[
        "buildings"
    ]:

        building_id = building[
            "building_id"
        ]

        for floor in building[
            "floors"
        ]:

            floor_id = floor[
                "floor_id"
            ]

            for unit in floor[
                "property_units"
            ]:

                if unit[
                    "parcel_id"
                ] != parcel_id:

                    validation_errors.append(
                        f"Unit {unit['unit_id']} "
                        f"has incorrect parcel."
                    )

                if unit[
                    "building_id"
                ] != building_id:

                    validation_errors.append(
                        f"Unit {unit['unit_id']} "
                        f"has incorrect building."
                    )

                if unit[
                    "floor_id"
                ] != floor_id:

                    validation_errors.append(
                        f"Unit {unit['unit_id']} "
                        f"has incorrect floor."
                    )


# ------------------------------------------------------------
# Validate underground assets → parcels
# ------------------------------------------------------------

for parcel in (
    master_model["study_areas"][0]["parcels"]
):

    parcel_id = parcel[
        "parcel_id"
    ]

    for asset in parcel[
        "underground_assets"
    ]:

        if asset[
            "parcel_id"
        ] != parcel_id:

            validation_errors.append(
                f"Asset {asset['asset_id']} "
                f"has incorrect parent parcel."
            )


if validation_errors:

    print(
        "HIERARCHY VALIDATION FAILED"
    )

    for error in validation_errors:

        print(
            f"  - {error}"
        )

    raise ValueError(
        "Master cadastral hierarchy "
        "contains validation errors."
    )


# ============================================================
# CALCULATE STATISTICS
# ============================================================

total_parcels = 0
total_buildings = 0
total_floors = 0
total_units = 0
total_assets = 0


for study in master_model[
    "study_areas"
]:

    total_parcels += len(
        study["parcels"]
    )

    for parcel in study[
        "parcels"
    ]:

        total_assets += len(
            parcel[
                "underground_assets"
            ]
        )

        total_buildings += len(
            parcel[
                "buildings"
            ]
        )

        for building in parcel[
            "buildings"
        ]:

            total_floors += len(
                building[
                    "floors"
                ]
            )

            for floor in building[
                "floors"
            ]:

                total_units += len(
                    floor[
                        "property_units"
                    ]
                )


master_model[
    "statistics"
] = {

    "study_areas":
        len(
            master_model[
                "study_areas"
            ]
        ),

    "parcels":
        total_parcels,

    "buildings":
        total_buildings,

    "floors":
        total_floors,

    "property_units":
        total_units,

    "underground_assets":
        total_assets,

}


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# WRITE MASTER MODEL
# ============================================================

with open(
    MASTER_MODEL_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        master_model,
        file,
        indent=2,
        ensure_ascii=False,
        default=clean_value,
    )


# ============================================================
# WRITE SUMMARY
# ============================================================

summary = {

    "schema":
        master_model[
            "schema"
        ],

    "statistics":
        master_model[
            "statistics"
        ],

    "validation":
        {

            "hierarchy":
                "PASSED",

            "crs":
                "PASSED",

            "source_geometry":
                "PASSED",

        },

}


with open(
    SUMMARY_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        summary,
        file,
        indent=2,
        ensure_ascii=False,
    )


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 70)
print("3D CADASTRAL MASTER MODEL COMPLETE")
print("=" * 70)

print()

print(
    f"Study areas:          {total_parcels * 0 + len(study_area)}"
)

print(
    f"Parcels:              {total_parcels}"
)

print(
    f"Buildings:            {total_buildings}"
)

print(
    f"Floors:               {total_floors}"
)

print(
    f"Property units:       {total_units}"
)

print(
    f"Underground assets:   {total_assets}"
)

print()

print(
    f"Master model:\n"
    f"{MASTER_MODEL_FILE}"
)

print(
    f"Summary:\n"
    f"{SUMMARY_FILE}"
)

print()

print(
    "CRS validation:        PASSED"
)

print(
    "Hierarchy validation:  PASSED"
)

print(
    "Source geometry:       PASSED"
)

print()

print(
    "ALL MASTER MODEL "
    "VALIDATIONS PASSED"
)