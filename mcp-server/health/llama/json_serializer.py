"""
solid-description: Serializes dictionaries to JSON-formatted strings.
solid-category: utility
solid-tags: [hook, llm]
"""

import json
from typing import Protocol


class JsonSerializing(Protocol):
    def serialize(self, obj: dict) -> str: ...


class JsonSerializer:
    """Boundary adapter: wraps json.dumps (stdlib, cannot be subclassed).

    json.dumps is a global stdlib function — this adapter satisfies
    the OCP Boundary Adapter exception.
    """

    def serialize(self, obj: dict) -> str:
        return json.dumps(obj)
