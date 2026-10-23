"""Defines loading of validated YAML mappings."""

from collections.abc import Mapping
from typing import Protocol

"""
solid-name: YamlMappingLoading
solid-category: abstraction
solid-description: Contract for loading YAML text as a validated string-keyed mapping.
"""


class YamlMappingLoading(Protocol):
    def load_mapping(self, text: str) -> Mapping[str, object] | None: ...
