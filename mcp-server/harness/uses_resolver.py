"""Resolves reusable step fragments for one declaring workflow file."""

from __future__ import annotations

from pathlib import Path

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.path_building import PathBuilding
from harness.uses_resolving import UsesResolving
from harness.workflow_config_resource import WorkflowConfigResource
from harness.workflow_config_resource_loading import WorkflowConfigResourceLoading
from harness.workflow_package_root_locating import WorkflowPackageRootLocating
from harness.workflow_resource_reference_creating import WorkflowResourceReferenceCreating


"""
solid-name: UsesResolver
solid-category: service
solid-spec: [SPEC-030, SPEC-035]
solid-description: Resolves and merges one reusable step fragment from its declaring package or legacy roots.
"""
class UsesResolver(UsesResolving):

    def __init__(
        self,
        resource_loader: WorkflowConfigResourceLoading,
        reference_factory: WorkflowResourceReferenceCreating,
        package_root_locator: WorkflowPackageRootLocating,
        path_builder: PathBuilding,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._resource_loader = resource_loader
        self._reference_factory = reference_factory
        self._package_root_locator = package_root_locator
        self._path_builder = path_builder
        self._error_factory = error_factory

    def resolve(self, raw_step: dict, flow_path: str, search_paths: list[str]) -> dict:
        uses = raw_step.get("uses")
        if uses is None:
            return raw_step

        declaring_file = self._path_builder.build(raw_step.get("__source_file") or flow_path)
        resource = self._find_fragment(uses, declaring_file, search_paths)
        merged = dict(resource.content)
        merged["__source_file"] = str(resource.path)
        for key, value in raw_step.items():
            if key not in ("uses", "__source_file"):
                merged[key] = value
        return merged

    def _find_fragment(
        self,
        uses: str,
        declaring_file: Path,
        search_paths: list[str],
    ) -> WorkflowConfigResource:
        resource = self._resource_loader.load(
            declaring_file,
            self._reference_factory.create(uses),
        )
        if resource is not None:
            return resource

        if self._package_root_locator.locate(declaring_file) is not None:
            raise self._error_factory.create(
                f"Unresolvable uses reference: '{uses}' not found relative to '{declaring_file}'"
            )
        for search_dir in search_paths:
            candidate = self._path_builder.build(search_dir, uses)
            resource = self._resource_loader.load(
                declaring_file,
                self._reference_factory.create(str(candidate)),
            )
            if resource is not None:
                return resource

        raise self._error_factory.create(
            f"Unresolvable uses reference: '{uses}' not found relative to the declaring file or search paths"
        )
