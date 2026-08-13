"""Validates workflow-step identity uniqueness."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.graph_step_field_reading import GraphStepFieldReading
from harness.step_identity_resolving import StepIdentityResolving
from harness.unique_step_identity_validating import UniqueStepIdentityValidating


"""
solid-name: UniqueStepIdentityValidator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Rejects duplicate workflow-step identifiers.
"""
class UniqueStepIdentityValidator(UniqueStepIdentityValidating):

    def __init__(
        self,
        identity_resolver: StepIdentityResolving,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._identity_resolver = identity_resolver
        self._error_factory = error_factory

    def validate(self, steps: list[GraphStepFieldReading]) -> None:
        seen_ids: set[str] = set()
        for step in steps:
            step_id = self._identity_resolver.resolve(step)
            if step_id in seen_ids:
                raise self._error_factory.create(f"Duplicate step ID: '{step_id}'")
            seen_ids.add(step_id)
