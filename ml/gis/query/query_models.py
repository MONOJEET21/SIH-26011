"""
Response models for the cadastral query engine.

The query engine deliberately returns structured responses so that
the same interface can later be used by:
    - FastAPI
    - an AI/LLM tool layer
    - the Cesium command layer
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class QueryResponse:
    success: bool
    query_type: str
    count: int = 0
    data: Any = None
    entity_ids: list[str] = field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def _extract_entity_id(item: dict[str, Any]) -> str | None:
        """
        Extract the ID belonging to the actual entity represented
        by this record.

        entity_type is preferred because cadastral records often
        contain several IDs at once, for example:

            property_unit:
                unit_id
                floor_id
                building_id
                parcel_id

        Without entity_type, a generic fallback could incorrectly
        select parcel_id instead of unit_id.
        """

        entity_type = item.get("entity_type")

        entity_id_fields = {
            "study_area": "study_area_id",
            "parcel": "parcel_id",
            "building": "building_id",
            "floor": "floor_id",
            "property_unit": "unit_id",
            "underground_asset": "asset_id",
        }

        preferred_field = entity_id_fields.get(entity_type)

        if preferred_field:
            value = item.get(preferred_field)

            if value is not None:
                return str(value)

        # Explicit generic identifiers are safe fallbacks.
        for field_name in (
            "entity_id",
            "id",
            "parcel_id",
            "building_id",
            "floor_id",
            "unit_id",
            "asset_id",
            "study_area_id",
        ):
            value = item.get(field_name)

            if value is not None:
                return str(value)

        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "query_type": self.query_type,
            "count": self.count,
            "data": self.data,
            "entity_ids": self.entity_ids,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def success_single(
        cls,
        query_type: str,
        data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> "QueryResponse":

        entity_id = cls._extract_entity_id(data)

        return cls(
            success=True,
            query_type=query_type,
            count=1,
            data=data,
            entity_ids=[entity_id] if entity_id else [],
            metadata=metadata or {},
        )

    @classmethod
    def success_collection(
        cls,
        query_type: str,
        data: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> "QueryResponse":

        entity_ids = []

        for item in data:
            entity_id = cls._extract_entity_id(item)

            if entity_id:
                entity_ids.append(entity_id)

        return cls(
            success=True,
            query_type=query_type,
            count=len(data),
            data=data,
            entity_ids=entity_ids,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        query_type: str,
        error: str,
        metadata: dict[str, Any] | None = None,
    ) -> "QueryResponse":

        return cls(
            success=False,
            query_type=query_type,
            count=0,
            data=None,
            entity_ids=[],
            error=error,
            metadata=metadata or {},
        )