"""
solid-description: Contract that defines YAML text parsing into Python objects.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Any, Protocol

import yaml


class YamlParsing(Protocol):
    """
    solid-description: Contract for parsing YAML-formatted text into Python objects.
    solid-category: abstraction
    """

    def parse(self, text: str) -> Any: ...


class SafeYamlParser:
    """
    solid-description: Parses YAML-formatted text into Python objects.
    solid-category: service
    """

    def parse(self, text: str) -> Any:
        result = yaml.safe_load(text)
        return result if result is not None else {}