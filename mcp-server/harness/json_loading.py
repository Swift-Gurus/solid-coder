"""
solid-description: Enables parsing of JSON-formatted text as Python objects.
solid-category: service
"""

from __future__ import annotations

import json
from typing import Any, Protocol


class JsonLoading(Protocol):
    """
    solid-description: Contract for parsing JSON-formatted text into Python objects.
    solid-category: abstraction
    """

    def safe_load(self, text: str) -> Any: ...


class JsonLoader:
    """
    solid-description: Loads JSON-formatted text as Python objects.
    solid-category: service
    """

    def safe_load(self, text: str) -> Any:
        return json.loads(text)
