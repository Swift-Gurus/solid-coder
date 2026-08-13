"""Resolves a prompt file from its declaring workflow file."""

from __future__ import annotations

from pathlib import Path

from harness.path_building import PathBuilding
from harness.step_declaration import StepDeclaration
from harness.workflow_resource_path_resolving import WorkflowResourcePathResolving
from harness.workflow_resource_reference_creating import WorkflowResourceReferenceCreating


"""
solid-name: PromptFilePathResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Resolves prompt-file references from their workflow context into readable filesystem paths.
"""
class PromptFilePathResolver:

    def __init__(
        self,
        path_builder: PathBuilding,
        resource_path_resolver: WorkflowResourcePathResolving,
        reference_factory: WorkflowResourceReferenceCreating,
    ) -> None:
        self._path_builder = path_builder
        self._resource_path_resolver = resource_path_resolver
        self._reference_factory = reference_factory

    def resolve(
        self,
        step: StepDeclaration,
        flow_file_path: str,
        prompt_file: str,
    ) -> Path:
        declaring_file = self._path_builder.build(step.source_file or flow_file_path)
        reference = self._reference_factory.create(prompt_file)
        return self._resource_path_resolver.resolve(declaring_file, reference)
