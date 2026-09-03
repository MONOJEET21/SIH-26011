"""
Cadastral query engine for the 3D ULPIN prototype.

This module provides a stable query interface over CadastralStore.

Current storage:
    cadastral_model.json -> CadastralStore

Future storage:
    PostgreSQL/PostGIS

The query layer deliberately hides storage details from:
    - FastAPI
    - AI/LLM tools
    - Cesium command layer
    - future PostGIS implementation
"""

from __future__ import annotations

from typing import Any

from .cadastral_store import CadastralStore
from .query_models import QueryResponse


class CadastralQueryEngine:
    """
    Query interface for the prototype 3D cadastral model.
    """

    def __init__(
        self,
        store: CadastralStore | None = None,
    ) -> None:
        self.store = store or CadastralStore()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _copy_record(
        record: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Return a shallow copy so callers cannot directly mutate
        the underlying store record.
        """
        return dict(record)

    @staticmethod
    def _with_context(
        record: dict[str, Any],
        *,
        entity_type: str,
        study_area_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Add common query metadata to an entity record.
        """
        result = dict(record)
        result["entity_type"] = entity_type

        if study_area_id is not None:
            result["study_area_id"] = study_area_id

        return result

    @staticmethod
    def _normalise_floor_code(
        floor_code: str,
    ) -> str:
        """
        Normalize common floor-code formats.

        Examples:
            F03 -> F03
            f03 -> F03
            B01 -> B01
            b01 -> B01
        """
        return str(floor_code).strip().upper()

    # ------------------------------------------------------------------
    # Direct entity queries
    # ------------------------------------------------------------------

    def get_parcel(
        self,
        parcel_id: str,
    ) -> QueryResponse:
        """
        Get a single parcel.
        """
        record = self.store.get_parcel_record(parcel_id)

        if record is None:
            return QueryResponse.failure(
                "get_parcel",
                f"Parcel not found: {parcel_id}",
            )

        result = self._with_context(
            self._copy_record(record),
            entity_type="parcel",
            study_area_id=self.store.get_parcel_study_area(parcel_id),
        )

        result["building_ids"] = (
            self.store.get_building_ids_in_parcel(parcel_id)
        )
        result["underground_asset_ids"] = (
            self.store.get_underground_asset_ids_in_parcel(parcel_id)
        )
        result["property_unit_count"] = len(
            self.store.get_unit_ids_in_parcel(parcel_id)
        )

        return QueryResponse.success_single(
            "get_parcel",
            result,
        )

    def get_building(
        self,
        building_id: str,
    ) -> QueryResponse:
        """
        Get a single building.
        """
        record = self.store.get_building_record(building_id)

        if record is None:
            return QueryResponse.failure(
                "get_building",
                f"Building not found: {building_id}",
            )

        parcel_id = self.store.get_building_parcel(building_id)
        study_area_id = self.store.get_building_study_area(building_id)

        result = self._with_context(
            self._copy_record(record),
            entity_type="building",
            study_area_id=study_area_id,
        )

        result["parcel_id"] = (
            result.get("parcel_id") or parcel_id
        )

        result["floor_ids"] = (
            self.store.get_floor_ids_in_building(building_id)
        )

        result["property_unit_count"] = len(
            self.store.get_unit_ids_in_building(building_id)
        )

        return QueryResponse.success_single(
            "get_building",
            result,
        )

    def get_floor(
        self,
        building_id: str,
        floor: int | str,
    ) -> QueryResponse:
        """
        Get a floor by building + floor number or floor code.

        Supported examples:

            get_floor("B001", 3)
            get_floor("B001", "F03")
            get_floor("B002", 0)
            get_floor("B002", "B01")
        """

        floor_ids = self.store.get_floor_ids_in_building(building_id)

        if not floor_ids:
            return QueryResponse.failure(
                "get_floor",
                f"Building not found or contains no floors: {building_id}",
            )

        selected_floor_id: str | None = None

        # --------------------------------------------------------------
        # Query by floor number
        # --------------------------------------------------------------

        if isinstance(floor, int):
            for floor_id in floor_ids:
                record = self.store.get_floor_record(floor_id)

                if record is None:
                    continue

                if record.get("floor_number") == floor:
                    selected_floor_id = floor_id
                    break

        # --------------------------------------------------------------
        # Query by floor code
        # --------------------------------------------------------------

        else:
            requested_code = self._normalise_floor_code(floor)

            for floor_id in floor_ids:
                record = self.store.get_floor_record(floor_id)

                if record is None:
                    continue

                record_floor_id = str(
                    record.get("floor_id", floor_id)
                ).upper()

                # Exact floor ID
                if record_floor_id == requested_code:
                    selected_floor_id = floor_id
                    break

                # Match suffix such as:
                # F03 -> B001_F03
                # B01 -> B002_B01
                if record_floor_id.endswith(
                    f"_{requested_code}"
                ):
                    selected_floor_id = floor_id
                    break

                # Also support an explicit floor_code field
                record_code = record.get("floor_code")

                if (
                    record_code is not None
                    and self._normalise_floor_code(record_code)
                    == requested_code
                ):
                    selected_floor_id = floor_id
                    break

        if selected_floor_id is None:
            return QueryResponse.failure(
                "get_floor",
                (
                    f"Floor {floor!r} not found in "
                    f"building {building_id}"
                ),
            )

        record = self.store.get_floor_record(selected_floor_id)

        if record is None:
            return QueryResponse.failure(
                "get_floor",
                f"Floor record unavailable: {selected_floor_id}",
            )

        parcel_id = self.store.get_floor_parcel(selected_floor_id)
        study_area_id = self.store.get_floor_study_area(
            selected_floor_id
        )

        result = self._with_context(
            self._copy_record(record),
            entity_type="floor",
            study_area_id=study_area_id,
        )

        result["building_id"] = (
            result.get("building_id")
            or self.store.get_floor_building(selected_floor_id)
        )

        result["parcel_id"] = (
            result.get("parcel_id")
            or parcel_id
        )

        result["property_unit_ids"] = (
            self.store.get_unit_ids_on_floor(selected_floor_id)
        )

        result["property_unit_count"] = len(
            result["property_unit_ids"]
        )

        return QueryResponse.success_single(
            "get_floor",
            result,
        )

    def get_property_unit(
        self,
        unit_id: str,
    ) -> QueryResponse:
        """
        Get a single property unit.
        """
        record = self.store.get_property_unit_record(unit_id)

        if record is None:
            return QueryResponse.failure(
                "get_property_unit",
                f"Property unit not found: {unit_id}",
            )

        floor_id = self.store.get_unit_floor(unit_id)
        building_id = self.store.get_unit_building(unit_id)
        parcel_id = self.store.get_unit_parcel(unit_id)
        study_area_id = self.store.get_unit_study_area(unit_id)

        result = self._with_context(
            self._copy_record(record),
            entity_type="property_unit",
            study_area_id=study_area_id,
        )

        result["floor_id"] = (
            result.get("floor_id")
            or floor_id
        )

        result["building_id"] = (
            result.get("building_id")
            or building_id
        )

        result["parcel_id"] = (
            result.get("parcel_id")
            or parcel_id
        )

        return QueryResponse.success_single(
            "get_property_unit",
            result,
        )

    # ------------------------------------------------------------------
    # Collection queries
    # ------------------------------------------------------------------

    def get_units_in_parcel(
        self,
        parcel_id: str,
    ) -> QueryResponse:
        """
        Get every property unit belonging to a parcel.
        """
        if self.store.get_parcel_record(parcel_id) is None:
            return QueryResponse.failure(
                "get_units_in_parcel",
                f"Parcel not found: {parcel_id}",
            )

        unit_ids = self.store.get_unit_ids_in_parcel(parcel_id)

        data: list[dict[str, Any]] = []

        for unit_id in unit_ids:
            record = self.store.get_property_unit_record(unit_id)

            if record is None:
                continue

            result = self._with_context(
                self._copy_record(record),
                entity_type="property_unit",
                study_area_id=self.store.get_unit_study_area(
                    unit_id
                ),
            )

            result["parcel_id"] = (
                result.get("parcel_id")
                or parcel_id
            )

            result["building_id"] = (
                result.get("building_id")
                or self.store.get_unit_building(unit_id)
            )

            result["floor_id"] = (
                result.get("floor_id")
                or self.store.get_unit_floor(unit_id)
            )

            data.append(result)

        return QueryResponse.success_collection(
            "get_units_in_parcel",
            data,
        )

    def get_units_in_building(
        self,
        building_id: str,
    ) -> QueryResponse:
        """
        Get every property unit belonging to a building.
        """
        if self.store.get_building_record(building_id) is None:
            return QueryResponse.failure(
                "get_units_in_building",
                f"Building not found: {building_id}",
            )

        unit_ids = self.store.get_unit_ids_in_building(
            building_id
        )

        data: list[dict[str, Any]] = []

        for unit_id in unit_ids:
            record = self.store.get_property_unit_record(unit_id)

            if record is None:
                continue

            result = self._with_context(
                self._copy_record(record),
                entity_type="property_unit",
                study_area_id=self.store.get_unit_study_area(
                    unit_id
                ),
            )

            result["building_id"] = (
                result.get("building_id")
                or building_id
            )

            result["parcel_id"] = (
                result.get("parcel_id")
                or self.store.get_unit_parcel(unit_id)
            )

            result["floor_id"] = (
                result.get("floor_id")
                or self.store.get_unit_floor(unit_id)
            )

            data.append(result)

        return QueryResponse.success_collection(
            "get_units_in_building",
            data,
        )

    def get_units_on_floor(
        self,
        building_id: str,
        floor: int | str,
    ) -> QueryResponse:
        """
        Get property units on a specific floor.
        """
        floor_response = self.get_floor(
            building_id,
            floor,
        )

        if not floor_response.success:
            return QueryResponse.failure(
                "get_units_on_floor",
                floor_response.error
                or "Unable to resolve floor.",
            )

        floor_id = floor_response.data["floor_id"]

        unit_ids = self.store.get_unit_ids_on_floor(floor_id)

        data: list[dict[str, Any]] = []

        for unit_id in unit_ids:
            record = self.store.get_property_unit_record(unit_id)

            if record is None:
                continue

            result = self._with_context(
                self._copy_record(record),
                entity_type="property_unit",
                study_area_id=self.store.get_unit_study_area(
                    unit_id
                ),
            )

            result["floor_id"] = (
                result.get("floor_id")
                or floor_id
            )

            result["building_id"] = (
                result.get("building_id")
                or self.store.get_unit_building(unit_id)
                or building_id
            )

            result["parcel_id"] = (
                result.get("parcel_id")
                or self.store.get_unit_parcel(unit_id)
            )

            data.append(result)

        return QueryResponse.success_collection(
            "get_units_on_floor",
            data,
        )

    def get_underground_assets(
        self,
        parcel_id: str,
    ) -> QueryResponse:
        """
        Get underground assets belonging to a parcel.
        """
        if self.store.get_parcel_record(parcel_id) is None:
            return QueryResponse.failure(
                "get_underground_assets",
                f"Parcel not found: {parcel_id}",
            )

        asset_ids = self.store.get_underground_asset_ids_in_parcel(
            parcel_id
        )

        data: list[dict[str, Any]] = []

        for asset_id in asset_ids:
            record = self.store.get_underground_asset_record(
                asset_id
            )

            if record is None:
                continue

            result = self._with_context(
                self._copy_record(record),
                entity_type="underground_asset",
                study_area_id=self.store.get_asset_study_area(
                    asset_id
                ),
            )

            result["parcel_id"] = (
                result.get("parcel_id")
                or parcel_id
            )

            data.append(result)

        return QueryResponse.success_collection(
            "get_underground_assets",
            data,
        )

    # ------------------------------------------------------------------
    # Spatial / hierarchy queries
    # ------------------------------------------------------------------

    def find_entities_in_parcel(
        self,
        parcel_id: str,
    ) -> QueryResponse:
        """
        Return all prototype cadastral entities associated with
        a parcel.

        Includes:

            parcel
            buildings
            floors
            property units
            underground assets

        For P001 this should return:

            1 parcel
            1 building
            5 floors
            15 property units
            1 underground asset

            total = 23
        """
        if self.store.get_parcel_record(parcel_id) is None:
            return QueryResponse.failure(
                "find_entities_in_parcel",
                f"Parcel not found: {parcel_id}",
            )

        data: list[dict[str, Any]] = []

        # --------------------------------------------------------------
        # Parcel
        # --------------------------------------------------------------

        parcel = self.store.get_parcel_record(parcel_id)

        if parcel is not None:
            data.append(
                self._with_context(
                    self._copy_record(parcel),
                    entity_type="parcel",
                    study_area_id=self.store.get_parcel_study_area(
                        parcel_id
                    ),
                )
            )

        # --------------------------------------------------------------
        # Buildings
        # --------------------------------------------------------------

        for building_id in self.store.get_building_ids_in_parcel(
            parcel_id
        ):
            building = self.store.get_building_record(building_id)

            if building is None:
                continue

            result = self._with_context(
                self._copy_record(building),
                entity_type="building",
                study_area_id=self.store.get_building_study_area(
                    building_id
                ),
            )

            result["parcel_id"] = (
                result.get("parcel_id")
                or parcel_id
            )

            data.append(result)

            # ----------------------------------------------------------
            # Floors
            # ----------------------------------------------------------

            for floor_id in self.store.get_floor_ids_in_building(
                building_id
            ):
                floor = self.store.get_floor_record(floor_id)

                if floor is None:
                    continue

                result = self._with_context(
                    self._copy_record(floor),
                    entity_type="floor",
                    study_area_id=self.store.get_floor_study_area(
                        floor_id
                    ),
                )

                result["building_id"] = (
                    result.get("building_id")
                    or building_id
                )

                result["parcel_id"] = (
                    result.get("parcel_id")
                    or parcel_id
                )

                data.append(result)

                # ------------------------------------------------------
                # Property units
                # ------------------------------------------------------

                for unit_id in self.store.get_unit_ids_on_floor(
                    floor_id
                ):
                    unit = self.store.get_property_unit_record(
                        unit_id
                    )

                    if unit is None:
                        continue

                    result = self._with_context(
                        self._copy_record(unit),
                        entity_type="property_unit",
                        study_area_id=self.store.get_unit_study_area(
                            unit_id
                        ),
                    )

                    result["floor_id"] = (
                        result.get("floor_id")
                        or floor_id
                    )

                    result["building_id"] = (
                        result.get("building_id")
                        or building_id
                    )

                    result["parcel_id"] = (
                        result.get("parcel_id")
                        or parcel_id
                    )

                    data.append(result)

        # --------------------------------------------------------------
        # Underground assets
        # --------------------------------------------------------------

        for asset_id in self.store.get_underground_asset_ids_in_parcel(
            parcel_id
        ):
            asset = self.store.get_underground_asset_record(asset_id)

            if asset is None:
                continue

            result = self._with_context(
                self._copy_record(asset),
                entity_type="underground_asset",
                study_area_id=self.store.get_asset_study_area(
                    asset_id
                ),
            )

            result["parcel_id"] = (
                result.get("parcel_id")
                or parcel_id
            )

            data.append(result)

        return QueryResponse.success_collection(
            "find_entities_in_parcel",
            data,
        )

    def find_entities_above_parcel(
        self,
        parcel_id: str,
    ) -> QueryResponse:
        """
        Return entities physically represented above the parcel
        in the prototype vertical model.

        Included:

            buildings
            above-ground floors
            property units

        Excluded:

            parcel itself
            underground assets
            basement floors

        Prototype vertical rule:

            z_min >= 0
            and
            z_max > 0
        """
        if self.store.get_parcel_record(parcel_id) is None:
            return QueryResponse.failure(
                "find_entities_above_parcel",
                f"Parcel not found: {parcel_id}",
            )

        data: list[dict[str, Any]] = []

        building_ids = self.store.get_building_ids_in_parcel(
            parcel_id
        )

        for building_id in building_ids:
            building = self.store.get_building_record(building_id)

            if building is None:
                continue

            building_z_min = building.get("z_min")
            building_z_max = building.get("z_max")

            if self._is_above_ground(
                building_z_min,
                building_z_max,
            ):
                result = self._with_context(
                    self._copy_record(building),
                    entity_type="building",
                    study_area_id=self.store.get_building_study_area(
                        building_id
                    ),
                )

                result["parcel_id"] = (
                    result.get("parcel_id")
                    or parcel_id
                )

                data.append(result)

            for floor_id in self.store.get_floor_ids_in_building(
                building_id
            ):
                floor = self.store.get_floor_record(floor_id)

                if floor is None:
                    continue

                floor_z_min = floor.get("z_min")
                floor_z_max = floor.get("z_max")

                if not self._is_above_ground(
                    floor_z_min,
                    floor_z_max,
                ):
                    continue

                # Explicitly exclude basement floors.
                if str(
                    floor.get("floor_type", "")
                ).upper() == "BASEMENT":
                    continue

                result = self._with_context(
                    self._copy_record(floor),
                    entity_type="floor",
                    study_area_id=self.store.get_floor_study_area(
                        floor_id
                    ),
                )

                result["building_id"] = (
                    result.get("building_id")
                    or building_id
                )

                result["parcel_id"] = (
                    result.get("parcel_id")
                    or parcel_id
                )

                data.append(result)

                for unit_id in self.store.get_unit_ids_on_floor(
                    floor_id
                ):
                    unit = self.store.get_property_unit_record(
                        unit_id
                    )

                    if unit is None:
                        continue

                    unit_z_min = unit.get("z_min")
                    unit_z_max = unit.get("z_max")

                    if not self._is_above_ground(
                        unit_z_min,
                        unit_z_max,
                    ):
                        continue

                    result = self._with_context(
                        self._copy_record(unit),
                        entity_type="property_unit",
                        study_area_id=self.store.get_unit_study_area(
                            unit_id
                        ),
                    )

                    result["floor_id"] = (
                        result.get("floor_id")
                        or floor_id
                    )

                    result["building_id"] = (
                        result.get("building_id")
                        or building_id
                    )

                    result["parcel_id"] = (
                        result.get("parcel_id")
                        or parcel_id
                    )

                    data.append(result)

        return QueryResponse.success_collection(
            "find_entities_above_parcel",
            data,
        )

    def find_underground_assets_below(
        self,
        parcel_id: str,
    ) -> QueryResponse:
        """
        Return underground assets represented below the parcel.

        Prototype rule:

            z_max <= 0
        """
        if self.store.get_parcel_record(parcel_id) is None:
            return QueryResponse.failure(
                "find_underground_assets_below",
                f"Parcel not found: {parcel_id}",
            )

        data: list[dict[str, Any]] = []

        for asset_id in self.store.get_underground_asset_ids_in_parcel(
            parcel_id
        ):
            asset = self.store.get_underground_asset_record(
                asset_id
            )

            if asset is None:
                continue

            z_max = asset.get("z_max")

            if not self._is_below_ground(z_max):
                continue

            result = self._with_context(
                self._copy_record(asset),
                entity_type="underground_asset",
                study_area_id=self.store.get_asset_study_area(
                    asset_id
                ),
            )

            result["parcel_id"] = (
                result.get("parcel_id")
                or parcel_id
            )

            data.append(result)

        return QueryResponse.success_collection(
            "find_underground_assets_below",
            data,
        )

    # ------------------------------------------------------------------
    # Model information
    # ------------------------------------------------------------------

    def get_statistics(self) -> QueryResponse:
        """
        Return cadastral model statistics.
        """
        return QueryResponse.success_single(
            "get_statistics",
            dict(self.store.get_statistics()),
        )

    def get_schema(self) -> QueryResponse:
        """
        Return cadastral model schema information.
        """
        return QueryResponse.success_single(
            "get_schema",
            dict(self.store.get_schema()),
        )

    # ------------------------------------------------------------------
    # Vertical helper methods
    # ------------------------------------------------------------------

    @staticmethod
    def _is_above_ground(
        z_min: Any,
        z_max: Any,
    ) -> bool:
        """
        Determine whether an entity occupies positive vertical space.
        """
        try:
            return (
                float(z_min) >= 0.0
                and float(z_max) > 0.0
            )
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _is_below_ground(
        z_max: Any,
    ) -> bool:
        """
        Determine whether an entity is at or below ground level.
        """
        try:
            return float(z_max) <= 0.0
        except (TypeError, ValueError):
            return False


# ----------------------------------------------------------------------
# Convenience functions
# ----------------------------------------------------------------------

def get_parcel(
    parcel_id: str,
) -> QueryResponse:
    return CadastralQueryEngine().get_parcel(parcel_id)


def get_building(
    building_id: str,
) -> QueryResponse:
    return CadastralQueryEngine().get_building(building_id)


def get_floor(
    building_id: str,
    floor: int | str,
) -> QueryResponse:
    return CadastralQueryEngine().get_floor(
        building_id,
        floor,
    )


def get_property_unit(
    unit_id: str,
) -> QueryResponse:
    return CadastralQueryEngine().get_property_unit(unit_id)


def get_units_in_parcel(
    parcel_id: str,
) -> QueryResponse:
    return CadastralQueryEngine().get_units_in_parcel(parcel_id)


def get_units_in_building(
    building_id: str,
) -> QueryResponse:
    return CadastralQueryEngine().get_units_in_building(
        building_id
    )


def get_units_on_floor(
    building_id: str,
    floor: int | str,
) -> QueryResponse:
    return CadastralQueryEngine().get_units_on_floor(
        building_id,
        floor,
    )


def get_underground_assets(
    parcel_id: str,
) -> QueryResponse:
    return CadastralQueryEngine().get_underground_assets(
        parcel_id
    )


def find_entities_in_parcel(
    parcel_id: str,
) -> QueryResponse:
    return CadastralQueryEngine().find_entities_in_parcel(
        parcel_id
    )


def find_entities_above_parcel(
    parcel_id: str,
) -> QueryResponse:
    return CadastralQueryEngine().find_entities_above_parcel(
        parcel_id
    )


def find_underground_assets_below(
    parcel_id: str,
) -> QueryResponse:
    return CadastralQueryEngine().find_underground_assets_below(
        parcel_id
    )


def get_statistics() -> QueryResponse:
    return CadastralQueryEngine().get_statistics()


def get_schema() -> QueryResponse:
    return CadastralQueryEngine().get_schema()


# ----------------------------------------------------------------------
# Smoke test
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import json

    engine = CadastralQueryEngine()

    print(
        json.dumps(
            engine.get_property_unit(
                "B001_F03_U0302"
            ).to_dict(),
            indent=2,
        )
    )

    print(
        json.dumps(
            engine.find_entities_in_parcel(
                "P001"
            ).to_dict(),
            indent=2,
        )
    )