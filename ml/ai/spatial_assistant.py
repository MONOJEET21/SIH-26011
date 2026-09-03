"""
High-level deterministic spatial assistant.

This is the bridge between:
    natural language
        ↓
    intent parser
        ↓
    controlled spatial tools
        ↓
    cadastral query engine

An LLM can be connected later without changing the underlying
cadastral query layer.
"""

from __future__ import annotations

from typing import Any

from ml.ai.intent_parser import parse_intent
from ml.ai.spatial_tools import SpatialToolRegistry


class SpatialAssistant:
    """
    Deterministic AI-assistant foundation.
    """

    def __init__(
        self,
        tool_registry: SpatialToolRegistry | None = None,
    ):
        self.tools = tool_registry or SpatialToolRegistry()

    def ask(self, question: str) -> dict[str, Any]:
        """
        Process one natural-language cadastral question.
        """

        try:
            intent = parse_intent(question)

            result = self.tools.execute(
                intent.intent,
                intent.parameters,
            )

            return {
                "success": result.get("success", False),
                "question": question,
                "intent": intent.to_dict(),
                "result": result,
            }

        except Exception as exc:
            return {
                "success": False,
                "question": question,
                "intent": None,
                "result": None,
                "error": str(exc),
            }

    def available_tools(self) -> list[str]:
        return self.tools.available_tools()


def ask_cadastral_question(question: str) -> dict[str, Any]:
    """
    Convenience function for one-off assistant queries.
    """

    assistant = SpatialAssistant()
    return assistant.ask(question)


if __name__ == "__main__":
    assistant = SpatialAssistant()

    examples = [
        "What's underground in P003?",
        "Show me the units on floor 3 of B001.",
        "Tell me about parcel P001.",
        "What is above parcel P002?",
    ]

    for question in examples:
        print("\nQUESTION:")
        print(question)

        response = assistant.ask(question)

        print("\nRESPONSE:")
        print(response)