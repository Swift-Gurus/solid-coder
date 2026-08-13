"""Validates inline-command workflow step declarations."""

from harness.command_step_field_reading import CommandStepFieldReading
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.step_field_validating import StepFieldValidating


"""
solid-name: CommandStepShapeValidator
solid-category: service
solid-spec: [SPEC-035]
solid-description: Validates the declared fields of inline-command workflow steps.
"""
class CommandStepShapeValidator(StepFieldValidating[CommandStepFieldReading]):
    def __init__(
        self,
        value_validator: StepFieldValidating[CommandStepFieldReading],
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._value_validator = value_validator
        self._error_factory = error_factory

    def validate(self, step: CommandStepFieldReading) -> None:
        self._value_validator.validate(step)
        if step.script_file is not None:
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'command' and must not declare 'file'"
            )
        if step.args is not None:
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'command' and must not declare 'args'"
            )
        if step.prompt or step.prompt_file:
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'command' and must not declare 'prompt' or 'prompt_file'"
            )
