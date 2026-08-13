"""Loads a required output schema resource."""

from __future__ import annotations

from pathlib import Path

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.workflow_config_resource_loading import WorkflowConfigResourceLoading
from harness.workflow_resource_reference_creating import WorkflowResourceReferenceCreating


"""
solid-name: OutputSchemaFileLoader
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Resolves and loads a required output schema while reporting invalid or missing resources.
"""
class OutputSchemaFileLoader:

    def __init__(
        self,
        resource_loader: WorkflowConfigResourceLoading,
        reference_factory: WorkflowResourceReferenceCreating,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._resource_loader = resource_loader
        self._reference_factory = reference_factory
        self._error_factory = error_factory

    def load(self, declaring_file: Path, reference: str, step_id: str, output_name: str) -> dict:
        resource_reference = self._reference_factory.create(reference)
        resource = self._resource_loader.load(declaring_file, resource_reference)
        if resource is None:
            raise self._error_factory.create(
                f"Step '{step_id}' output '{output_name}' schema_file not found "
                f"or not valid JSON: '{reference}'"
            )
        return resource.content
