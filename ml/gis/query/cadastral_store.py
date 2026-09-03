"""
Indexed storage layer for the 3D cadastral model.

This module is intentionally independent of FastAPI/PostGIS.

Current prototype:
    cadastral_model.json -> CadastralStore

Future architecture:
    PostgreSQL/PostGIS -> compatible query engine

The query interface should remain stable even when the underlying
storage changes.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "outputs"
    / "cadastral"
    / "cadastral_model.json"
)


class CadastralStore:
    """
    Loads and indexes the 3D cadastral model.

    Indexes are created for:

        study areas
        parcels
        buildings
        floors
        property units
        underground assets

    Relationship indexes are also created for fast hierarchical queries.
    """

    def __init__(self, model_path: str | Path | None = None) -> None:
        if model_path is None:
            environment_path = os.getenv("CADASTRAL_MODEL_PATH")

            if environment_path:
                model_path = Path(environment_path)
            else:
                model_path = DEFAULT_MODEL_PATH

        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Cadastral model not found: {self.model_path}"
            )

        self.model: dict[str, Any] = self._load_model()

        self.schema: dict[str, Any] = self.model.get("schema", {})
        self.statistics: dict[str, Any] = self.model.get("statistics", {})

        self._build_indexes()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_model(self) -> dict[str, Any]:
        """Load the cadastral JSON model."""

        try:
            with self.model_path.open("r", encoding="utf-8") as file:
                model = json.load(file)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON in cadastral model: {self.model_path}"
            ) from exc

        if not isinstance(model, dict):
            raise ValueError(
                "Cadastral model root must be a JSON object."
            )

        if "study_areas" not in model:
            raise ValueError(
                "Cadastral model is missing required 'study_areas'."
            )

        if not isinstance(model["study_areas"], list):
            raise ValueError(
                "'study_areas' must be a list."
            )

        return model

    # ------------------------------------------------------------------
    # Index creation
    # ------------------------------------------------------------------

    def _build_indexes(self) -> None:
        """Build entity and relationship indexes."""

        self.study_areas: dict[str, dict[str, Any]] = {}
        self.parcels: dict[str, dict[str, Any]] = {}
        self.buildings: dict[str, dict[str, Any]] = {}
        self.floors: dict[str, dict[str, Any]] = {}
        self.property_units: dict[str, dict[str, Any]] = {}
        self.underground_assets: dict[str, dict[str, Any]] = {}

        # Parent relationships
        self.parcel_to_study_area: dict[str, str] = {}

        self.building_to_parcel: dict[str, str] = {}
        self.building_to_study_area: dict[str, str] = {}

        self.floor_to_building: dict[str, str] = {}
        self.floor_to_parcel: dict[str, str] = {}
        self.floor_to_study_area: dict[str, str] = {}

        self.unit_to_floor: dict[str, str] = {}
        self.unit_to_building: dict[str, str] = {}
        self.unit_to_parcel: dict[str, str] = {}
        self.unit_to_study_area: dict[str, str] = {}

        self.asset_to_parcel: dict[str, str] = {}
        self.asset_to_study_area: dict[str, str] = {}

        # Child relationships
        self.parcel_to_buildings: dict[str, list[str]] = {}
        self.parcel_to_assets: dict[str, list[str]] = {}

        self.building_to_floors: dict[str, list[str]] = {}

        self.floor_to_units: dict[str, list[str]] = {}

        self.parcel_to_units: dict[str, list[str]] = {}

        for study_area in self.model["study_areas"]:
            study_area_id = self._required_id(
                study_area,
                "study_area_id",
                "study area",
            )

            self._register_unique(
                self.study_areas,
                study_area_id,
                study_area,
                "study area",
            )

            self._index_study_area(study_area, study_area_id)

    def _index_study_area(
        self,
        study_area: dict[str, Any],
        study_area_id: str,
    ) -> None:
        """Index everything belonging to a study area."""

        parcels = study_area.get("parcels", [])

        if not isinstance(parcels, list):
            raise ValueError(
                f"Study area {study_area_id}: 'parcels' must be a list."
            )

        for parcel in parcels:
            parcel_id = self._required_id(
                parcel,
                "parcel_id",
                "parcel",
            )

            self._register_unique(
                self.parcels,
                parcel_id,
                parcel,
                "parcel",
            )

            self.parcel_to_study_area[parcel_id] = study_area_id
            self.parcel_to_buildings.setdefault(parcel_id, [])
            self.parcel_to_assets.setdefault(parcel_id, [])
            self.parcel_to_units.setdefault(parcel_id, [])

            self._index_parcel(
                parcel,
                parcel_id,
                study_area_id,
            )

    def _index_parcel(
        self,
        parcel: dict[str, Any],
        parcel_id: str,
        study_area_id: str,
    ) -> None:
        """Index buildings and underground assets belonging to a parcel."""

        buildings = parcel.get("buildings", [])

        if not isinstance(buildings, list):
            raise ValueError(
                f"Parcel {parcel_id}: 'buildings' must be a list."
            )

        for building in buildings:
            building_id = self._required_id(
                building,
                "building_id",
                "building",
            )

            referenced_parcel = building.get("parcel_id")

            if referenced_parcel and referenced_parcel != parcel_id:
                raise ValueError(
                    f"Building {building_id} references parcel "
                    f"{referenced_parcel}, but is nested under {parcel_id}."
                )

            self._register_unique(
                self.buildings,
                building_id,
                building,
                "building",
            )

            self.building_to_parcel[building_id] = parcel_id
            self.building_to_study_area[building_id] = study_area_id

            self.parcel_to_buildings[parcel_id].append(building_id)
            self.building_to_floors.setdefault(building_id, [])

            self._index_building(
                building,
                building_id,
                parcel_id,
                study_area_id,
            )

        assets = parcel.get("underground_assets", [])

        if not isinstance(assets, list):
            raise ValueError(
                f"Parcel {parcel_id}: 'underground_assets' must be a list."
            )

        for asset in assets:
            asset_id = self._required_id(
                asset,
                "asset_id",
                "underground asset",
            )

            referenced_parcel = asset.get("parcel_id")

            if referenced_parcel and referenced_parcel != parcel_id:
                raise ValueError(
                    f"Underground asset {asset_id} references parcel "
                    f"{referenced_parcel}, but is nested under {parcel_id}."
                )

            self._register_unique(
                self.underground_assets,
                asset_id,
                asset,
                "underground asset",
            )

            self.asset_to_parcel[asset_id] = parcel_id
            self.asset_to_study_area[asset_id] = study_area_id

            self.parcel_to_assets[parcel_id].append(asset_id)

    def _index_building(
        self,
        building: dict[str, Any],
        building_id: str,
        parcel_id: str,
        study_area_id: str,
    ) -> None:
        """Index floors and property units belonging to a building."""

        floors = building.get("floors", [])

        if not isinstance(floors, list):
            raise ValueError(
                f"Building {building_id}: 'floors' must be a list."
            )

        for floor in floors:
            floor_id = self._required_id(
                floor,
                "floor_id",
                "floor",
            )

            referenced_building = floor.get("building_id")

            if (
                referenced_building
                and referenced_building != building_id
            ):
                raise ValueError(
                    f"Floor {floor_id} references building "
                    f"{referenced_building}, but is nested under "
                    f"{building_id}."
                )

            self._register_unique(
                self.floors,
                floor_id,
                floor,
                "floor",
            )

            self.floor_to_building[floor_id] = building_id
            self.floor_to_parcel[floor_id] = parcel_id
            self.floor_to_study_area[floor_id] = study_area_id

            self.building_to_floors[building_id].append(floor_id)
            self.floor_to_units.setdefault(floor_id, [])

            self._index_floor(
                floor,
                floor_id,
                building_id,
                parcel_id,
                study_area_id,
            )

    def _index_floor(
        self,
        floor: dict[str, Any],
        floor_id: str,
        building_id: str,
        parcel_id: str,
        study_area_id: str,
    ) -> None:
        """Index property units belonging to a floor."""

        units = floor.get("property_units", [])

        if not isinstance(units, list):
            raise ValueError(
                f"Floor {floor_id}: 'property_units' must be a list."
            )

        for unit in units:
            unit_id = self._required_id(
                unit,
                "unit_id",
                "property unit",
            )

            referenced_floor = unit.get("floor_id")
            referenced_building = unit.get("building_id")
            referenced_parcel = unit.get("parcel_id")

            if (
                referenced_floor
                and referenced_floor != floor_id
            ):
                raise ValueError(
                    f"Property unit {unit_id} references floor "
                    f"{referenced_floor}, but is nested under {floor_id}."
                )

            if (
                referenced_building
                and referenced_building != building_id
            ):
                raise ValueError(
                    f"Property unit {unit_id} references building "
                    f"{referenced_building}, but is nested under "
                    f"{building_id}."
                )

            if (
                referenced_parcel
                and referenced_parcel != parcel_id
            ):
                raise ValueError(
                    f"Property unit {unit_id} references parcel "
                    f"{referenced_parcel}, but is nested under {parcel_id}."
                )

            self._register_unique(
                self.property_units,
                unit_id,
                unit,
                "property unit",
            )

            self.unit_to_floor[unit_id] = floor_id
            self.unit_to_building[unit_id] = building_id
            self.unit_to_parcel[unit_id] = parcel_id
            self.unit_to_study_area[unit_id] = study_area_id

            self.floor_to_units[floor_id].append(unit_id)
            self.parcel_to_units[parcel_id].append(unit_id)

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _required_id(
        record: dict[str, Any],
        field_name: str,
        entity_name: str,
    ) -> str:
        """Get and validate a required identifier."""

        value = record.get(field_name)

        if value is None or str(value).strip() == "":
            raise ValueError(
                f"{entity_name} is missing required field '{field_name}'."
            )

        return str(value)

    @staticmethod
    def _register_unique(
        index: dict[str, dict[str, Any]],
        entity_id: str,
        record: dict[str, Any],
        entity_name: str,
    ) -> None:
        """Register an entity and reject duplicate IDs."""

        if entity_id in index:
            raise ValueError(
                f"Duplicate {entity_name} ID detected: {entity_id}"
            )

        index[entity_id] = record

    # ------------------------------------------------------------------
    # Direct accessors
    # ------------------------------------------------------------------

    def get_parcel_record(self, parcel_id: str) -> dict[str, Any] | None:
        return self.parcels.get(parcel_id)

    def get_building_record(self, building_id: str) -> dict[str, Any] | None:
        return self.buildings.get(building_id)

    def get_floor_record(self, floor_id: str) -> dict[str, Any] | None:
        return self.floors.get(floor_id)

    def get_property_unit_record(
        self,
        unit_id: str,
    ) -> dict[str, Any] | None:
        return self.property_units.get(unit_id)

    def get_underground_asset_record(
        self,
        asset_id: str,
    ) -> dict[str, Any] | None:
        return self.underground_assets.get(asset_id)

    # ------------------------------------------------------------------
    # Relationship accessors
    # ------------------------------------------------------------------

    def get_building_ids_in_parcel(self, parcel_id: str) -> list[str]:
        return list(self.parcel_to_buildings.get(parcel_id, []))

    def get_underground_asset_ids_in_parcel(
        self,
        parcel_id: str,
    ) -> list[str]:
        return list(self.parcel_to_assets.get(parcel_id, []))

    def get_floor_ids_in_building(self, building_id: str) -> list[str]:
        return list(self.building_to_floors.get(building_id, []))

    def get_unit_ids_on_floor(self, floor_id: str) -> list[str]:
        return list(self.floor_to_units.get(floor_id, []))

    def get_unit_ids_in_building(self, building_id: str) -> list[str]:
        unit_ids: list[str] = []

        for floor_id in self.get_floor_ids_in_building(building_id):
            unit_ids.extend(self.get_unit_ids_on_floor(floor_id))

        return unit_ids

    def get_unit_ids_in_parcel(self, parcel_id: str) -> list[str]:
        return list(self.parcel_to_units.get(parcel_id, []))

    # ------------------------------------------------------------------
    # Context accessors
    # ------------------------------------------------------------------

    def get_parcel_study_area(self, parcel_id: str) -> str | None:
        return self.parcel_to_study_area.get(parcel_id)

    def get_building_parcel(self, building_id: str) -> str | None:
        return self.building_to_parcel.get(building_id)

    def get_building_study_area(self, building_id: str) -> str | None:
        return self.building_to_study_area.get(building_id)

    def get_floor_building(self, floor_id: str) -> str | None:
        return self.floor_to_building.get(floor_id)

    def get_floor_parcel(self, floor_id: str) -> str | None:
        return self.floor_to_parcel.get(floor_id)

    def get_floor_study_area(self, floor_id: str) -> str | None:
        return self.floor_to_study_area.get(floor_id)

    def get_unit_floor(self, unit_id: str) -> str | None:
        return self.unit_to_floor.get(unit_id)

    def get_unit_building(self, unit_id: str) -> str | None:
        return self.unit_to_building.get(unit_id)

    def get_unit_parcel(self, unit_id: str) -> str | None:
        return self.unit_to_parcel.get(unit_id)

    def get_unit_study_area(self, unit_id: str) -> str | None:
        return self.unit_to_study_area.get(unit_id)

    def get_asset_parcel(self, asset_id: str) -> str | None:
        return self.asset_to_parcel.get(asset_id)

    def get_asset_study_area(self, asset_id: str) -> str | None:
        return self.asset_to_study_area.get(asset_id)

    # ------------------------------------------------------------------
    # Model information
    # ------------------------------------------------------------------

    def get_schema(self) -> dict[str, Any]:
        return dict(self.schema)

    def get_statistics(self) -> dict[str, Any]:
        return dict(self.statistics)