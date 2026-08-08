"""Resolves reusable step fragments for one declaring workflow file."""

from __future__ import annotations

from pathlib import Path

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.path_building import PathBuilding
from harness.uses_resolving import UsesResolving
from harness.workflow_package_root_locating import WorkflowPackageRootLocating
from harness.workflow_resource_path_resolving import WorkflowResourcePathResolving
from scoring.yaml_config_file_loader import ConfigFileLoading


"""
solid-name: UsesResolver
solid-category: service
solid-spec: [SPEC-030, SPEC-035]
solid-description: Resolves and merges one reusable step fragment from its declaring package or legacy roots.
"""
class UsesResolver(UsesResolving):

    def __init__(
        self,
        file_loader: ConfigFileLoading,
        resource_path_resolver: WorkflowResourcePathResolving,
        package_root_locator: WorkflowPackageRootLocating,
        path_builder: PathBuilding,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._file_loader = file_loader
        self._resource_path_resolver = resource_path_resolver
        self._package_root_locator = package_root_locator
        self._path_builder = path_builder
        self._error_factory = error_factory

    def resolve(self, raw_step: dict, flow_path: str, search_paths: list[str]) -> dict:
        uses = raw_step.get("uses")
        if uses is None:
            return raw_step

        declaring_file = self._path_builder.build(raw_step.get("__source_file") or flow_path)
        fragment, fragment_path = self._find_fragment(uses, declaring_file, search_paths)
        merged = dict(fragment)
        merged["__source_file"] = str(fragment_path)
        for key, value in raw_step.items():
            if key not in ("uses", "__source_file"):
                merged[key] = value
        return merged

    def _find_fragment(
        self,
        uses: str,
        declaring_file: Path,
        search_paths: list[str],
    ) -> tuple[dict, Path]:
        relative_candidate = self._resource_path_resolver.resolve(declaring_file, uses)
        result = self._file_loader.load(relative_candidate)
        if result is not None:
            return result, relative_candidate

        if self._package_root_locator.locate(declaring_file) is not None:
            raise self._error_factory.create(
                f"Unresolvable uses reference: '{uses}' not found relative to '{declaring_file}'"
            )
        for search_dir in search_paths:
            candidate = self._path_builder.build(search_dir, uses)
            result = self._file_loader.load(candidate)
            if result is not None:
                return result, candidate

        raise self._error_factory.create(
            f"Unresolvable uses reference: '{uses}' not found relative to the declaring file or search paths"
        )
