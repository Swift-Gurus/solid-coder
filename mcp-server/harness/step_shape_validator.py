"""Validates workflow-step declarations by their declared type."""

from __future__ import annotations

from harness.step_declaration import StepDeclaration
from harness.step_field_validating import StepFieldValidating
from harness.step_field_validator_registration import StepFieldValidatorRegistration
from harness.step_shape_validating import StepShapeValidating


"""
solid-name: StepShapeValidator
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Validates workflow steps using the field validator registered for each declared type.
"""
class StepShapeValidator(StepShapeValidating):

    def __init__(
        self,
        registrations: list[StepFieldValidatorRegistration],
        default: StepFieldValidating,
    ) -> None:
        self._registrations = registrations
        self._default = default

    def validate(self, steps: list[StepDeclaration]) -> None:
        for step in steps:
            registration = next(
                (
                    item
                    for item in self._registrations
                    if item.step_type == step.type
                ),
                None,
            )
            validator = registration.validator if registration is not None else self._default
            validator.validate(step)
