"""Resolves the workflow file that declared a step."""

from __future__ import annotations

from pathlib import Path

from harness.path_building import PathBuilding


"""
solid-name: StepDeclaringFileResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Selects and normalizes the source workflow path attached to an expanded step.
"""
class StepDeclaringFileResolver:

    def __init__(self, path_builder: PathBuilding) -> None:
        self._path_builder = path_builder

    def resolve(self, source_file: str | None, flow_file_path: str) -> Path:
        return self._path_builder.build(source_file or flow_file_path)
