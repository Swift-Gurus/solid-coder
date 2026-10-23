"""
solid-description: Provides JSON deserialization with graceful handling of invalid input.
solid-category: utility
solid-tags: [hook, llm]
"""

import json
from typing import Protocol

"""
solid-name: JsonDeserializing
solid-category: abstraction
solid-description: Contract for deserializing JSON data while safely handling invalid input.
"""


class JsonDeserializing(Protocol):
    def deserialize(self, raw: bytes) -> dict | None: ...


"""
solid-name: JsonDeserializer
solid-category: utility
solid-description: Deserializes JSON data and returns no result when the input is invalid.
"""


class JsonDeserializer:
    """Boundary adapter: wraps json.loads (stdlib, cannot be subclassed).

    json.loads is a global stdlib function — this adapter satisfies
    the OCP Boundary Adapter exception.
    """

    def deserialize(self, raw: bytes) -> dict | None:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
