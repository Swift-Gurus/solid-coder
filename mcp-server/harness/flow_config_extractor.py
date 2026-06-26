"""
solid-description: Extract configuration values from a flow definition.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Protocol


class FlowConfigExtracting(Protocol):
    """
    solid-description: Contract for extracting configuration values from a flow definition.
    solid-category: abstraction
    """

    def extract_name(self, raw: dict) -> str: ...
    def extract_max_turns(self, raw: dict) -> int: ...
    def extract_steps(self, raw: dict) -> list[dict]: ...


class FlowConfigExtractor:
    """
    solid-description: Extract flow configuration values with sensible defaults.
    solid-category: service
    """

    def extract_name(self, raw: dict) -> str:
        return raw.get("name", "")

    def extract_max_turns(self, raw: dict) -> int:
        return raw.get("max_turns", 10)

    def extract_steps(self, raw: dict) -> list[dict]:
        return raw.get("steps") or []
