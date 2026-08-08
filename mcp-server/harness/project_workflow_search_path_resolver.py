"""Provides project-owned workflow search directories."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from harness.flow_search_path_resolving import FlowSearchPathResolving


"""
solid-name: ProjectWorkflowSearchPathResolver
solid-category: service
solid-spec: [SPEC-031, SPEC-035]
solid-description: Resolves ordered package and legacy workflow search directories owned by the active project.
"""
class ProjectWorkflowSearchPathResolver(FlowSearchPathResolving):

    def __init__(self, project_directory: Callable[[], Path]) -> None:
        self._project_directory = project_directory

    def resolve(self) -> list[Path]:
        project_root = self._project_directory() / ".solid-coder"
        return [
            project_root / "workflows",
            project_root / "harness" / "flows",
        ]
