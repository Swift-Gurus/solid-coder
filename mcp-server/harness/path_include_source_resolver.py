"""Resolves a relative path-based workflow include."""

from __future__ import annotations

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.include_source import IncludeSource
from harness.path_include_entry_reading import PathIncludeEntryReading
from harness.step_declaring_file_resolving import StepDeclaringFileResolving
from harness.step_source_annotating import StepSourceAnnotating
from harness.workflow_config_resource_loading import WorkflowConfigResourceLoading
from harness.workflow_include_runtime_parsing import WorkflowIncludeRuntimeParsing
from harness.workflow_resource_reference_creating import WorkflowResourceReferenceCreating
from harness.workflow_output_declaration_parser import WorkflowOutputDeclarationParser


"""
solid-name: PathIncludeSourceResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Resolves a declaring-file-relative workflow include into an annotated include source.
"""
class PathIncludeSourceResolver:

    def __init__(
        self,
        entry_reader: PathIncludeEntryReading,
        declaring_file_resolver: StepDeclaringFileResolving,
        resource_loader: WorkflowConfigResourceLoading,
        reference_factory: WorkflowResourceReferenceCreating,
        source_annotator: StepSourceAnnotating,
        runtime_parser: WorkflowIncludeRuntimeParsing,
        output_parser: WorkflowOutputDeclarationParser,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._entry_reader = entry_reader
        self._declaring_file_resolver = declaring_file_resolver
        self._resource_loader = resource_loader
        self._reference_factory = reference_factory
        self._source_annotator = source_annotator
        self._runtime_parser = runtime_parser
        self._output_parser = output_parser
        self._error_factory = error_factory

    def resolve(self, entry: dict, flow_file_path: str, search_paths: list[str]) -> IncludeSource | None:
        path_entry = self._entry_reader.read(entry)
        if path_entry is None:
            return None

        declaring_file = self._declaring_file_resolver.resolve(
            path_entry.source_file,
            flow_file_path,
        )
        resource = self._resource_loader.load(
            declaring_file,
            self._reference_factory.create(path_entry.path),
        )
        if resource is None:
            raise self._error_factory.create(
                f"Unresolvable include: '{path_entry.path}' not found relative to '{declaring_file}'"
            )
        source_path = str(resource.path)
        return IncludeSource(
            alias=path_entry.alias,
            steps=self._source_annotator.annotate(resource.content.get("steps") or [], source_path),
            flow_path=source_path,
            runtime=self._runtime_parser.parse(entry, resource.content),
            identity=source_path,
            label=source_path,
            source_path=source_path,
            workflow_id=resource.content.get("id"),
            outputs=self._output_parser.parse(
                resource.content.get("outputs"),
                source_path,
            ),
        )
