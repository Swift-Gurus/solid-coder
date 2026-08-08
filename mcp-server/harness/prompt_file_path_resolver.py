"""Resolves a prompt file from its declaring workflow file."""

from __future__ import annotations

from pathlib import Path

from harness.path_building import PathBuilding
from harness.workflow_resource_path_resolving import WorkflowResourcePathResolving


"""
solid-name: PromptFilePathResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Resolves a prompt-file reference through declaring-file and package containment policies.
"""
class PromptFilePathResolver:

    def __init__(
        self,
        path_builder: PathBuilding,
        resource_path_resolver: WorkflowResourcePathResolving,
    ) -> None:
        self._path_builder = path_builder
        self._resource_path_resolver = resource_path_resolver

    def resolve(self, step: dict, flow_file_path: str, prompt_file: str) -> Path:
        declaring_file = self._path_builder.build(step.get("__source_file") or flow_file_path)
        return self._resource_path_resolver.resolve(declaring_file, prompt_file)
