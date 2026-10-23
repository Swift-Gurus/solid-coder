"""Validates typed workflow steps that own compact metrics."""

from harness.co_located_metric_owner_validating import (
    CoLocatedMetricOwnerValidating,
)
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.step_declaration import StepDeclaration

"""
solid-name: CoLocatedMetricOwnerValidator
solid-category: service
solid-spec: [SPEC-058]
solid-description: Enforces identified non-iterating agent ownership for co-located measurements.
"""


class CoLocatedMetricOwnerValidator(CoLocatedMetricOwnerValidating):
    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def validate(self, owner: StepDeclaration) -> str:
        owner_id = owner.id
        if not isinstance(owner_id, str) or not owner_id:
            raise self._error_factory.create(
                "A step declaring metrics must have a non-empty id"
            )
        if owner.type != "agent":
            raise self._error_factory.create(
                f"Step '{owner_id}' must be type 'agent' to declare metrics"
            )
        if owner.for_each is not None:
            raise self._error_factory.create(
                f"Step '{owner_id}' with for_each must use explicit metric steps"
            )
        return owner_id
