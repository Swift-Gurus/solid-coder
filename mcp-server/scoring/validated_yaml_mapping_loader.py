"""Loads YAML text as a validated mapping."""

from collections.abc import Mapping
from typing import Optional

from scoring.yaml_loader import YamlLoading
from scoring.yaml_mapping_loading import YamlMappingLoading


"""
solid-name: ValidatedYamlMappingLoader
solid-category: boundary-adapter
solid-description: Validates decoded YAML values and exposes string-keyed mapping access.
"""
class ValidatedYamlMappingLoader(YamlMappingLoading):
    def __init__(self, yaml_loader: YamlLoading) -> None:
        self._yaml_loader = yaml_loader

    def load_mapping(self, text: str) -> Optional[Mapping[str, object]]:
        parsed = self._yaml_loader.safe_load(text)
        if not isinstance(parsed, Mapping):
            return None
        if not all(isinstance(key, str) for key in parsed):
            return None
        return parsed
