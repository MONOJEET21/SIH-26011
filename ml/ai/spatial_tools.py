"""
Controlled tool layer for the AI spatial assistant.

Every operation here maps directly to an existing
CadastralQueryEngine operation.

The AI layer should never access the cadastral model directly.
"""

from __future__ import annotations

from typing import Any, Callable

from ml.gis.query.cadastral_queries import CadastralQueryEngine


class SpatialToolRegistry:
    """
    Registry of safe cadastral operations exposed to the AI.
    """

    def __init__(self, engine: CadastralQueryEngine | None = None):
        self.engine = engine or CadastralQueryEngine()

        self._tools: dict[str, Callable[..., Any]] = {
            "get_parcel": self.engine.get_parcel,
            "get_building": self.engine.get_building,
            "get_floor": self.engine.get_floor,
            "get_property_unit": self.engine.get_property_unit,
            "get_units_in_parcel": self.engine.get_units_in_parcel,
            "get_units_in_building": self.engine.get_units_in_building,
            "get_units_on_floor": self.engine.get_units_on_floor,
            "get_underground_assets": self.engine.get_underground_assets,
            "find_entities_in_parcel": self.engine.find_entities_in_parcel,
            "find_entities_above_parcel": self.engine.find_entities_above_parcel,
            "find_underground_assets_below": (
                self.engine.find_underground_assets_below
            ),
            "get_statistics": self.engine.get_statistics,
            "get_schema": self.engine.get_schema,
        }

    def available_tools(self) -> list[str]:
        """Return all operations exposed to the AI."""
        return sorted(self._tools.keys())

    def execute(
        self,
        intent: str,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute one approved cadastral operation.

        Args:
            intent: Registered operation name.
            parameters: Arguments for that operation.

        Returns:
            Serialized QueryResponse.
        """

        if intent not in self._tools:
            raise ValueError(
                f"Unsupported spatial tool: {intent}"
            )

        parameters = parameters or {}

        tool = self._tools[intent]

        result = tool(**self._normalise_parameters(
            intent,
            parameters,
        ))

        return result.to_dict()

    @staticmethod
    def _normalise_parameters(
        intent: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Normalize parameters before calling the query engine.
        """

        params = dict(parameters)

        if intent in {
            "get_parcel",
            "get_units_in_parcel",
            "get_underground_assets",
            "find_entities_in_parcel",
            "find_entities_above_parcel",
            "find_underground_assets_below",
        }:
            if "parcel_id" not in params:
                raise ValueError(
                    f"{intent} requires parcel_id."
                )

        if intent in {
            "get_building",
            "get_units_in_building",
        }:
            if "building_id" not in params:
                raise ValueError(
                    f"{intent} requires building_id."
                )

        if intent in {
            "get_floor",
            "get_units_on_floor",
        }:
            if "building_id" not in params:
                raise ValueError(
                    f"{intent} requires building_id."
                )

            if "floor" not in params:
                raise ValueError(
                    f"{intent} requires floor."
                )

        if intent == "get_property_unit":
            if "unit_id" not in params:
                raise ValueError(
                    "get_property_unit requires unit_id."
                )

        return params


def get_tool_definitions() -> list[dict[str, Any]]:
    """
    Return machine-readable tool definitions.

    These definitions will later be supplied to an LLM as
    function/tool specifications.
    """

    return [
        {
            "name": "get_parcel",
            "description": "Retrieve a cadastral parcel.",
            "parameters": {
                "parcel_id": "string",
            },
        },
        {
            "name": "get_building",
            "description": "Retrieve a building and its cadastral context.",
            "parameters": {
                "building_id": "string",
            },
        },
        {
            "name": "get_floor",
            "description": "Retrieve a floor within a building.",
            "parameters": {
                "building_id": "string",
                "floor": "integer or floor code",
            },
        },
        {
            "name": "get_property_unit",
            "description": "Retrieve one property unit.",
            "parameters": {
                "unit_id": "string",
            },
        },
        {
            "name": "get_units_in_parcel",
            "description": "Find property units within a parcel.",
            "parameters": {
                "parcel_id": "string",
            },
        },
        {
            "name": "get_units_in_building",
            "description": "Find property units within a building.",
            "parameters": {
                "building_id": "string",
            },
        },
        {
            "name": "get_units_on_floor",
            "description": "Find property units on a floor.",
            "parameters": {
                "building_id": "string",
                "floor": "integer or floor code",
            },
        },
        {
            "name": "get_underground_assets",
            "description": "Retrieve underground assets associated with a parcel.",
            "parameters": {
                "parcel_id": "string",
            },
        },
        {
            "name": "find_entities_in_parcel",
            "description": "Find all cadastral entities inside a parcel.",
            "parameters": {
                "parcel_id": "string",
            },
        },
        {
            "name": "find_entities_above_parcel",
            "description": "Find entities above a parcel.",
            "parameters": {
                "parcel_id": "string",
            },
        },
        {
            "name": "find_underground_assets_below",
            "description": "Find underground assets below a parcel.",
            "parameters": {
                "parcel_id": "string",
            },
        },
        {
            "name": "get_statistics",
            "description": "Retrieve cadastral dataset statistics.",
            "parameters": {},
        },
        {
            "name": "get_schema",
            "description": "Retrieve the cadastral data schema.",
            "parameters": {},
        },
    ]