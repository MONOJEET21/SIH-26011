import json
import re
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.ai.gemini_service import (
    generate_grounded_answer,
    parse_spatial_question,
)


router = APIRouter(
    prefix="/ai",
    tags=["BHUYAAM AI"],
)


# =========================================================
# DATA FILE
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[4]

GEOJSON_PATH = (
    PROJECT_ROOT
    / "backend"
    / "data"
    / "guwahati_buildings_3d.geojson"
)


# =========================================================
# REQUEST / RESPONSE
# =========================================================

class AIQueryRequest(BaseModel):
    question: str


class AIQueryResponse(BaseModel):
    answer: str
    intent: str
    building_id: Optional[str] = None
    building_name: Optional[str] = None
    data: dict[str, Any]


# =========================================================
# LOAD REAL GEOJSON DATA
# =========================================================

def load_buildings() -> list[dict[str, Any]]:

    if not GEOJSON_PATH.exists():
        raise FileNotFoundError(
            f"GeoJSON data file not found: {GEOJSON_PATH}"
        )

    with open(
        GEOJSON_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        geojson = json.load(file)

    return geojson.get("features", [])


# =========================================================
# NORMALIZE TEXT
# =========================================================

def normalize_text(value: Any) -> str:

    if value is None:
        return ""

    value = str(value).lower()

    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


# =========================================================
# GET BUILDING SEARCHABLE TEXT
# =========================================================

def building_search_text(
    feature: dict[str, Any],
) -> str:

    props = feature.get(
        "properties",
        {},
    )

    values = [
        props.get("building_id"),
        props.get("source_name"),
        props.get("display_name"),
        props.get("source_type"),
        props.get("source_osm_id"),
    ]

    return normalize_text(
        " ".join(
            str(value)
            for value in values
            if value is not None
        )
    )


# =========================================================
# TOKEN MATCH SCORE
# =========================================================

def calculate_match_score(
    query: str,
    feature: dict[str, Any],
) -> float:

    query_normalized = normalize_text(query)

    searchable = building_search_text(
        feature
    )

    if not query_normalized:
        return 0.0

    # Exact phrase match
    if query_normalized in searchable:
        return 100.0

    query_tokens = set(
        query_normalized.split()
    )

    searchable_tokens = set(
        searchable.split()
    )

    if not query_tokens:
        return 0.0

    matches = len(
        query_tokens.intersection(
            searchable_tokens
        )
    )

    return (
        matches / len(query_tokens)
    ) * 100


# =========================================================
# SEARCH BUILDINGS DYNAMICALLY
# =========================================================

def search_buildings(
    buildings: list[dict[str, Any]],
    building_query: str,
    limit: int = 5,
) -> list[dict[str, Any]]:

    scored_results = []

    for feature in buildings:

        score = calculate_match_score(
            building_query,
            feature,
        )

        if score > 0:

            scored_results.append(
                (
                    score,
                    feature,
                )
            )

    scored_results.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        feature
        for score, feature
        in scored_results[:limit]
    ]


# =========================================================
# BUILD VERIFIED DATA
# =========================================================

def build_building_data(
    feature: dict[str, Any],
) -> dict[str, Any]:

    props = feature.get(
        "properties",
        {},
    )

    return {
        "building_id":
            props.get("building_id"),

        "source_name":
            props.get("source_name"),

        "display_name":
            props.get("display_name"),

        "source_type":
            props.get("source_type"),

        "source_building_levels":
            props.get(
                "source_building_levels"
            ),

        "source_height_m":
            props.get(
                "source_height_m"
            ),

        "height_m":
            props.get(
                "height_m"
            ),

        "floors_estimated":
            props.get(
                "floors_estimated"
            ),

        "data_status":
            props.get(
                "data_status"
            ),

        "identity_status":
            props.get(
                "identity_status"
            ),
    }


# =========================================================
# MAIN AI ENDPOINT
# =========================================================

@router.post(
    "/query",
    response_model=AIQueryResponse,
)
def query_bhuyaam_ai(
    payload: AIQueryRequest,
):

    question = payload.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    # -----------------------------------------------------
    # 1. GEMINI UNDERSTANDS QUESTION
    # -----------------------------------------------------

    try:

        parsed = parse_spatial_question(
            question
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Gemini could not process "
                f"the question: {str(exc)}"
            ),
        )

    intent = parsed.get(
        "intent",
        "unknown",
    )

    building_query = parsed.get(
        "building_query",
        "",
    )

    # -----------------------------------------------------
    # 2. LOAD REAL SPATIAL DATA
    # -----------------------------------------------------

    try:

        buildings = load_buildings()

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    # -----------------------------------------------------
    # 3. SEARCH REAL BUILDINGS
    # -----------------------------------------------------

    matches = search_buildings(
        buildings=buildings,
        building_query=building_query,
    )

    # -----------------------------------------------------
    # 4. BUILD VERIFIED RESULT
    # -----------------------------------------------------

    if intent == "unknown":

        verified_result = {
            "found": False,
            "message":
                "The question could not be mapped "
                "to a supported spatial query.",
        }

    elif not matches:

        verified_result = {
            "found": False,
            "message":
                "No matching building was found "
                "in the currently loaded spatial dataset.",

            "searched_for":
                building_query,
        }

    elif len(matches) > 1:

        verified_result = {
            "found": True,

            "multiple_matches": True,

            "match_count":
                len(matches),

            "matches": [
                build_building_data(
                    feature
                )
                for feature in matches
            ],
        }

    else:

        building_data = build_building_data(
            matches[0]
        )

        verified_result = {
            "found": True,

            "multiple_matches": False,

            "building":
                building_data,
        }

    # -----------------------------------------------------
    # 5. GEMINI GENERATES GROUNDED ANSWER
    # -----------------------------------------------------

    try:

        answer = generate_grounded_answer(
            question=question,
            database_result=verified_result,
        )

    except Exception:

        if verified_result.get("found"):

            answer = (
                "The requested building information "
                "was found in the spatial dataset."
            )

        else:

            answer = verified_result.get(
                "message",
                "No matching information was found.",
            )

    # -----------------------------------------------------
    # 6. SELECT BEST BUILDING FOR FRONTEND
    # -----------------------------------------------------

    selected_building = None

    if (
        verified_result.get("found")
        and not verified_result.get(
            "multiple_matches",
            False,
        )
    ):

        selected_building = (
            verified_result
            .get("building")
        )

    # -----------------------------------------------------
    # 7. RETURN RESPONSE
    # -----------------------------------------------------

    return AIQueryResponse(
        answer=answer,

        intent=intent,

        building_id=(
            selected_building.get(
                "building_id"
            )
            if selected_building
            else None
        ),

        building_name=(
            selected_building.get(
                "display_name"
            )
            if selected_building
            else None
        ),

        data=verified_result,
    )