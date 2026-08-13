"""Resolves validated workflow-step identifiers."""

from __future__ import annotations

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.graph_step_field_reading import GraphStepFieldReading
from harness.step_identity_resolving import StepIdentityResolving


"""
solid-name: StepIdentityResolver
solid-category: service
solid-spec: [SPEC-027]
solid-description: Resolves a non-empty string identifier from a workflow-step declaration.
"""
class StepIdentityResolver(StepIdentityResolving):
    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def resolve(self, step: GraphStepFieldReading) -> str:
        if not isinstance(step.id, str) or not step.id:
            raise self._error_factory.create("Step is missing required field 'id'")
        return step.id
