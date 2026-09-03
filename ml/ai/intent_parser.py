"""
Deterministic intent parser for the 3D ULPIN cadastral assistant.

This module converts supported natural-language requests into
validated structured commands.

No LLM is used here yet. This gives us a safe, testable contract
before connecting an actual language model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class SpatialIntent:
    intent: str
    parameters: dict[str, Any]
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "parameters": self.parameters,
            "confidence": self.confidence,
        }


def _normalise(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _extract_id(text: str, pattern: str) -> str | None:
    """
    Extract the actual entity ID from a regex.

    The supplied regex must contain the entity ID as its
    first capturing group.
    """
    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return None

    value = match.group(1)

    if not value:
        return None

    return value.upper()


def parse_intent(text: str) -> SpatialIntent:
    """
    Parse a supported cadastral question.

    Raises:
        ValueError: if the request cannot be mapped to a supported
                    cadastral operation.
    """

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Query must be a non-empty string.")

    query = _normalise(text)

    # =========================================================
    # STATISTICS
    # =========================================================

    if any(
        phrase in query
        for phrase in (
            "statistics",
            "dataset statistics",
            "system statistics",
            "how many parcels",
            "how many buildings",
            "how many floors",
            "how many property units",
        )
    ):
        return SpatialIntent(
            intent="get_statistics",
            parameters={},
        )

    # =========================================================
    # SCHEMA
    # =========================================================

    if any(
        phrase in query
        for phrase in (
            "schema",
            "data model",
            "cadastral model structure",
        )
    ):
        return SpatialIntent(
            intent="get_schema",
            parameters={},
        )

    # =========================================================
    # PROPERTY UNIT LOOKUP
    # =========================================================

    unit_id = _extract_id(
        query,
        r"\b(B\d+_F\d+_U\d+)\b",
    )

    if unit_id:
        return SpatialIntent(
            intent="get_property_unit",
            parameters={
                "unit_id": unit_id,
            },
        )

    # =========================================================
    # BUILDING ID
    # =========================================================

    building_id = _extract_id(
        query,
        r"\b(?:building\s*)?(B\d+)\b",
    )

    # =========================================================
    # FLOOR + BUILDING
    # =========================================================

    floor_match = re.search(
        r"\b(?:floor|level)\s*(?:number\s*)?(\d+)\b",
        query,
        re.IGNORECASE,
    )

    if floor_match and building_id:

        floor_number = int(floor_match.group(1))

        if any(
            phrase in query
            for phrase in (
                "property units",
                "units",
                "properties",
            )
        ):
            return SpatialIntent(
                intent="get_units_on_floor",
                parameters={
                    "building_id": building_id,
                    "floor": floor_number,
                },
            )

        return SpatialIntent(
            intent="get_floor",
            parameters={
                "building_id": building_id,
                "floor": floor_number,
            },
        )

    # =========================================================
    # BUILDING LOOKUP / BUILDING UNITS
    # =========================================================

    if building_id:

        if (
            "property units" in query
            or "units" in query
        ):
            return SpatialIntent(
                intent="get_units_in_building",
                parameters={
                    "building_id": building_id,
                },
            )

        return SpatialIntent(
            intent="get_building",
            parameters={
                "building_id": building_id,
            },
        )

    # =========================================================
    # PARCEL ID
    # =========================================================

    parcel_id = _extract_id(
        query,
        r"\b(?:parcel\s*)?(P\d+)\b",
    )

    if parcel_id:

        # -----------------------------------------------------
        # Underground
        # -----------------------------------------------------

        if any(
            phrase in query
            for phrase in (
                "underground",
                "below",
                "beneath",
                "under",
            )
        ):
            return SpatialIntent(
                intent="find_underground_assets_below",
                parameters={
                    "parcel_id": parcel_id,
                },
            )

        # -----------------------------------------------------
        # Above parcel
        # -----------------------------------------------------

        if any(
            phrase in query
            for phrase in (
                "above",
                "on top of",
                "over",
            )
        ):
            return SpatialIntent(
                intent="find_entities_above_parcel",
                parameters={
                    "parcel_id": parcel_id,
                },
            )

        # -----------------------------------------------------
        # Property units in parcel
        # -----------------------------------------------------

        if (
            "property units" in query
            or "units in parcel" in query
            or "units inside parcel" in query
        ):
            return SpatialIntent(
                intent="get_units_in_parcel",
                parameters={
                    "parcel_id": parcel_id,
                },
            )

        # -----------------------------------------------------
        # All entities in parcel
        # -----------------------------------------------------

        if any(
            phrase in query
            for phrase in (
                "inside",
                "within",
                "in the parcel",
                "in parcel",
                "what is in",
                "what's in",
                "what is inside",
                "what's inside",
            )
        ):
            return SpatialIntent(
                intent="find_entities_in_parcel",
                parameters={
                    "parcel_id": parcel_id,
                },
            )

        # -----------------------------------------------------
        # Default parcel lookup
        # -----------------------------------------------------

        return SpatialIntent(
            intent="get_parcel",
            parameters={
                "parcel_id": parcel_id,
            },
        )

    # =========================================================
    # UNSUPPORTED QUERY
    # =========================================================

    raise ValueError(
        "Unable to understand the cadastral request. "
        "Supported entities include parcels, buildings, floors, "
        "property units and underground assets."
    )


if __name__ == "__main__":
    examples = [
        "What's underground in P003?",
        "Show me the units on floor 3 of B001.",
        "Tell me about parcel P001.",
        "What is above parcel P002?",
        "Show me building B002.",
        "Show me property unit B001_F03_U0302.",
    ]

    for example in examples:
        print()
        print("QUESTION:", example)

        try:
            result = parse_intent(example)
            print("INTENT:", result.to_dict())
        except Exception as exc:
            print("ERROR:", exc)