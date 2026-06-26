"""
solid-description: Contract for resolving uses references in raw step dictionaries.
solid-category: abstraction
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

from scoring.yaml_config_file_loader import YamlConfigFileLoader
from harness.models import FlowValidationError


class UsesResolving(Protocol):
    """
    solid-description: Contract for resolving uses references in raw step dictionaries.
    solid-category: abstraction
    """

    def resolve(self, raw_step: dict, flow_path: str, search_paths: list[str]) -> dict: ...


class UsesResolver:
    """
    solid-description: Resolves uses references in raw step dictionaries.
    solid-category: service
    """

    def __init__(self, file_loader: YamlConfigFileLoader) -> None:
        self._file_loader = file_loader

    def resolve(self, raw_step: dict, flow_path: str, search_paths: list[str]) -> dict:
        uses = raw_step.get("uses")
        if uses is None:
            return raw_step

        fragment = self._find_fragment(uses, flow_path, search_paths)
        merged = dict(fragment)
        for key, value in raw_step.items():
            if key != "uses":
                merged[key] = value
        return merged

    def _find_fragment(self, uses: str, flow_path: str, search_paths: list[str]) -> dict:
        filename = os.path.basename(uses)

        for search_dir in search_paths:
            candidate = Path(search_dir) / filename
            result = self._file_loader.load(candidate)
            if result is not None:
                return result

        flow_dir = Path(os.path.abspath(flow_path)).parent
        result = self._file_loader.load(flow_dir / filename)
        if result is not None:
            return result

        raise FlowValidationError(
            f"Unresolvable uses reference: '{uses}' not found in search_paths or alongside flow file"
        )
