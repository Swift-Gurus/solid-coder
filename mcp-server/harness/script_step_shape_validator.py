"""Validates the field set of a script workflow step."""

from __future__ import annotations

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.script_step_field_reading import ScriptStepFieldReading
from harness.step_field_validating import StepFieldValidating


"""
solid-name: ScriptStepShapeValidator
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Validates prompt compatibility and delegates execution-value validation for script steps.
"""
class ScriptStepShapeValidator(StepFieldValidating[ScriptStepFieldReading]):
    def __init__(
        self,
        value_validator: StepFieldValidating[ScriptStepFieldReading],
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._value_validator = value_validator
        self._error_factory = error_factory

    def validate(self, step: ScriptStepFieldReading) -> None:
        if step.prompt or step.prompt_file:
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'script' and must not declare 'prompt' or 'prompt_file'"
            )
        self._value_validator.validate(step)
