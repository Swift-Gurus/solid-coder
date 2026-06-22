"""
solid-description: Deserializes JSON bytes to dictionaries.
solid-category: utility
solid-tags: [hook, llm]
"""

import json
from typing import Optional, Protocol


class JsonDeserializing(Protocol):
    def deserialize(self, raw: bytes) -> Optional[dict]: ...


class JsonDeserializer:
    """Boundary adapter: wraps json.loads (stdlib, cannot be subclassed).

    json.loads is a global stdlib function — this adapter satisfies
    the OCP Boundary Adapter exception.
    """

    def deserialize(self, raw: bytes) -> Optional[dict]:
        try:
            return json.loads(raw)
        except Exception:
            return None
