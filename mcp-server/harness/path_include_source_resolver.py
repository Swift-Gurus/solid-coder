"""Resolves a relative path-based workflow include."""

from __future__ import annotations

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.include_source import IncludeSource
from harness.include_source_creating import IncludeSourceCreating
from harness.step_declaring_file_resolving import StepDeclaringFileResolving
from harness.step_source_annotating import StepSourceAnnotating
from harness.workflow_config_resource_loading import WorkflowConfigResourceLoading
from harness.workflow_resource_reference_creating import WorkflowResourceReferenceCreating


"""
solid-name: PathIncludeSourceResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Loads a package-contained subflow relative to the workflow file declaring its include entry.
"""
class PathIncludeSourceResolver:

    def __init__(
        self,
        declaring_file_resolver: StepDeclaringFileResolving,
        resource_loader: WorkflowConfigResourceLoading,
        reference_factory: WorkflowResourceReferenceCreating,
        source_annotator: StepSourceAnnotating,
        error_factory: FlowValidationErrorCreating,
        source_factory: IncludeSourceCreating,
    ) -> None:
        self._declaring_file_resolver = declaring_file_resolver
        self._resource_loader = resource_loader
        self._reference_factory = reference_factory
        self._source_annotator = source_annotator
        self._error_factory = error_factory
        self._source_factory = source_factory

    def resolve(self, entry: dict, flow_file_path: str, search_paths: list[str]) -> IncludeSource | None:
        include_path = entry.get("include")
        if not isinstance(include_path, str):
            return None

        declaring_file = self._declaring_file_resolver.resolve(
            entry.get("__source_file"),
            flow_file_path,
        )
        resource = self._resource_loader.load(
            declaring_file,
            self._reference_factory.create(include_path),
        )
        if resource is None:
            raise self._error_factory.create(
                f"Unresolvable include: '{include_path}' not found relative to '{declaring_file}'"
            )
        source_path = str(resource.path)
        return self._source_factory.create(
            alias=entry["as"],
            steps=self._source_annotator.annotate(resource.content.get("steps") or [], source_path),
            flow_path=source_path,
            identity=source_path,
            label=source_path,
            source_path=source_path,
            workflow_id=resource.content.get("id"),
        )
