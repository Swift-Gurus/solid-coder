"""
solid-description: Parses tool call argument payloads from LLM responses.
solid-category: utility
solid-tags: [hook, llm]
"""

import json
from typing import Protocol


class ToolCallArgsParsing(Protocol):
    def parse(self, tool_call: dict) -> dict: ...


class ToolCallParser:
    """Extracts and JSON-parses the arguments from a tool_call dict."""

    def parse(self, tool_call: dict) -> dict:
        raw = tool_call.get("function", {}).get("arguments", "{}")
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
        try:
            return dict(raw) if raw else {}
        except (TypeError, ValueError):
            return {}
