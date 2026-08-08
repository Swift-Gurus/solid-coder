"""Defines loading of validated YAML mappings."""

from typing import Mapping, Optional, Protocol


"""
solid-name: YamlMappingLoading
solid-category: abstraction
solid-description: Contract for loading YAML text as a validated string-keyed mapping.
"""
class YamlMappingLoading(Protocol):
    def load_mapping(self, text: str) -> Optional[Mapping[str, object]]: ...
