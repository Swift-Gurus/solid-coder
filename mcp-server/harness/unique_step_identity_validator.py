"""Resolves workflow-step identities and validates their uniqueness."""

from harness.graph_step_field_reading import GraphStepFieldReading
from harness.step_identity_resolving import StepIdentityResolving
from harness.unique_step_identity_validating import UniqueStepIdentityValidating
from harness.unique_string_validating import UniqueStringValidating


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
        identity_validator: UniqueStringValidating,
    ) -> None:
        self._identity_resolver = identity_resolver
        self._identity_validator = identity_validator

    def validate(self, steps: list[GraphStepFieldReading]) -> None:
        self._identity_validator.validate(
            [self._identity_resolver.resolve(step) for step in steps],
            "step ID",
        )
