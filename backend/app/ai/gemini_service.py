import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it to backend/.env"
    )

client = genai.Client(api_key=GEMINI_API_KEY)


def _extract_json(text: str) -> dict[str, Any]:
    """
    Extract JSON safely even if Gemini wraps it in markdown.
    """

    text = text.strip()

    if text.startswith("```"):
        text = (
            text.replace("```json", "")
            .replace("```JSON", "")
            .replace("```", "")
            .strip()
        )

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("Gemini did not return valid JSON.")

    return json.loads(text[start:end + 1])


def parse_spatial_question(question: str) -> dict[str, Any]:
    """
    Gemini understands WHAT the user is asking.

    It does NOT invent factual answers.
    It only extracts the intent and search information.
    """

    prompt = f"""
You are the intent understanding component of BHUYAAM AI,
a 3D cadastral and spatial intelligence system.

The user asked:

"{question}"

The spatial dataset contains buildings with fields such as:

- building_id
- source_name
- display_name
- source_type
- source_building_levels
- source_height_m
- height_m
- floors_estimated
- data_status
- identity_status

Understand the user's question and return ONLY JSON.

Allowed intents:

- building_floor_count
- building_height
- building_details
- building_type
- building_id
- building_search
- unknown

Return exactly this JSON structure:

{{
  "intent": "one allowed intent",
  "building_query": "the building/entity/location name extracted from the question",
  "confidence": 0.0
}}

Rules:

1. NEVER answer the user's factual question.
2. NEVER invent building names or values.
3. Extract the most useful building search phrase.
4. For questions like:
   "How many floors does X have?"
   use building_floor_count.
5. For questions about building height,
   use building_height.
6. For general information about a building,
   use building_details.
7. If no building/entity can be identified,
   building_query may be an empty string.
8. Return JSON only.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return _extract_json(response.text)


def generate_grounded_answer(
    question: str,
    database_result: dict[str, Any],
) -> str:
    """
    Gemini converts verified dataset information into
    a natural language answer.
    """

    prompt = f"""
You are BHUYAAM AI, an assistant for a 3D cadastral
and spatial intelligence platform.

User question:

"{question}"

VERIFIED DATA FROM THE SPATIAL DATASET:

{json.dumps(database_result, indent=2, default=str)}

Answer naturally and concisely.

CRITICAL RULES:

- Use ONLY the verified data above.
- NEVER invent facts, names, numbers or measurements.
- If found is false, explain that no matching building
  was found in the currently loaded spatial dataset.
- If multiple buildings match, explain that clearly.
- Do not mention internal implementation details
  such as GeoJSON parsing unless useful.
- Keep the answer suitable for speaking aloud.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text.strip()