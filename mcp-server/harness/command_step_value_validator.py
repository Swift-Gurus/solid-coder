"""Validates inline-command step values."""

from __future__ import annotations

from harness.command_step_field_reading import CommandStepFieldReading
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.step_field_validating import StepFieldValidating


"""
solid-name: CommandStepValueValidator
solid-category: service
solid-spec: [SPEC-035]
solid-description: Validates command text and executor values declared by an inline-command step.
"""
class CommandStepValueValidator(StepFieldValidating[CommandStepFieldReading]):
    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def validate(self, step: CommandStepFieldReading) -> None:
        if not isinstance(step.command, str) or not step.command:
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'command' and must declare a non-empty command string"
            )
        if step.executor is not None and (
            not isinstance(step.executor, str) or not step.executor
        ):
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'command' and 'executor' must be a non-empty string"
            )
