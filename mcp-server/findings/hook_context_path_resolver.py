"""Resolves requested health-check context paths."""

from pathlib import Path

from findings.hook_context_path_resolving import HookContextPathResolving
from harness.path_building import PathBuilding


"""
solid-name: HookContextPathResolver
solid-category: service
solid-description: Resolves requested hook context locations.
"""
class HookContextPathResolver(HookContextPathResolving):
    def __init__(self, path_builder: PathBuilding) -> None:
        self._path_builder = path_builder

    def resolve(self, output_dir: str) -> Path:
        return self._path_builder.build(output_dir, "hook-input.json")
