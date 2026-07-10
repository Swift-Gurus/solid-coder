"""
solid-description: Serializes a dict to a string representation.
solid-category: utility
"""

import json
from typing import Optional, Protocol


class JsonSerializing(Protocol):
    def serialize(self, doc: dict, indent: Optional[int] = None) -> str: ...


class JsonSerializer:
    """Boundary adapter: wraps json.dumps for injection into writers."""

    def serialize(self, doc: dict, indent: Optional[int] = None) -> str:
        return json.dumps(doc, indent=indent)
