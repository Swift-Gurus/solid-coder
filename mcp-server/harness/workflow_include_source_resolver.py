"""Resolves a stable workflow-ID include."""

from __future__ import annotations

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.include_source import IncludeSource
from harness.include_source_creating import IncludeSourceCreating
from harness.step_source_annotating import StepSourceAnnotating
from harness.workflow_catalog_resolving import WorkflowCatalogResolving
from scoring.yaml_config_file_loader import ConfigFileLoading


"""
solid-name: WorkflowIncludeSourceResolver
solid-category: service
solid-spec: [SPEC-035]
solid-description: Loads an included workflow by globally unique catalog ID and records its stable provenance.
"""
class WorkflowIncludeSourceResolver:

    def __init__(
        self,
        file_loader: ConfigFileLoading,
        catalog_resolver: WorkflowCatalogResolving,
        source_annotator: StepSourceAnnotating,
        error_factory: FlowValidationErrorCreating,
        source_factory: IncludeSourceCreating,
    ) -> None:
        self._file_loader = file_loader
        self._catalog_resolver = catalog_resolver
        self._source_annotator = source_annotator
        self._error_factory = error_factory
        self._source_factory = source_factory

    def resolve(self, entry: dict, flow_file_path: str, search_paths: list[str]) -> IncludeSource | None:
        declaration = entry.get("include")
        if not isinstance(declaration, dict):
            return None
        workflow_id = declaration.get("workflow")
        if not isinstance(workflow_id, str) or not workflow_id:
            raise self._error_factory.create(
                "Workflow include must declare a non-empty 'workflow' ID"
            )

        source = self._catalog_resolver.resolve(workflow_id, search_paths)
        if source is None:
            raise self._error_factory.create(
                f"Unresolvable workflow include: '{workflow_id}'"
            )
        raw = self._file_loader.load(source.entry_path)
        if raw is None:
            raise self._error_factory.create(
                f"Workflow include '{workflow_id}' could not load '{source.entry_path}'"
            )
        source_path = str(source.entry_path)
        return self._source_factory.create(
            alias=entry["as"],
            steps=self._source_annotator.annotate(raw.get("steps") or [], source_path),
            flow_path=source_path,
            identity=source_path,
            label=workflow_id,
            source_path=source_path,
            workflow_id=workflow_id,
        )
