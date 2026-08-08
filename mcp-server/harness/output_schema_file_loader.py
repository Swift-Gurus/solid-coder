"""Loads a required output schema resource."""

from __future__ import annotations

from pathlib import Path

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.workflow_resource_path_resolving import WorkflowResourcePathResolving
from scoring.yaml_config_file_loader import ConfigFileLoading


"""
solid-name: OutputSchemaFileLoader
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Resolves and loads a required output schema while reporting invalid or missing resources.
"""
class OutputSchemaFileLoader:

    def __init__(
        self,
        file_loader: ConfigFileLoading,
        resource_path_resolver: WorkflowResourcePathResolving,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._file_loader = file_loader
        self._resource_path_resolver = resource_path_resolver
        self._error_factory = error_factory

    def load(self, declaring_file: Path, reference: str, step_id: str, output_name: str) -> dict:
        schema_path = self._resource_path_resolver.resolve(declaring_file, reference)
        schema = self._file_loader.load(schema_path)
        if schema is None:
            raise self._error_factory.create(
                f"Step '{step_id}' output '{output_name}' schema_file not found "
                f"or not valid JSON: '{reference}'"
            )
        return schema
