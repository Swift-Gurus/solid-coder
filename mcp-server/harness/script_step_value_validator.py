"""Validates script-step execution values."""

from __future__ import annotations

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.script_step_field_reading import ScriptStepFieldReading
from harness.step_field_validating import StepFieldValidating


"""
solid-name: ScriptStepValueValidator
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Validates structured and legacy execution values declared by a script workflow step.
"""
class ScriptStepValueValidator(StepFieldValidating[ScriptStepFieldReading]):
    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def validate(self, step: ScriptStepFieldReading) -> None:
        if step.script_file is not None:
            self._validate_script_file(step)
            return
        self._validate_legacy_command(step)

    def _validate_script_file(self, step: ScriptStepFieldReading) -> None:
        if not isinstance(step.script_file, str) or not step.script_file:
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'script' and must declare a non-empty 'file'"
            )
        if step.command is not None:
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'script' and must not mix 'file' with 'command'"
            )
        arguments = step.args if step.args is not None else []
        if not isinstance(arguments, list) or not all(
            isinstance(argument, str) for argument in arguments
        ):
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'script' and 'args' must be a list of strings"
            )
        self._validate_executor(step)

    def _validate_legacy_command(self, step: ScriptStepFieldReading) -> None:
        if not isinstance(step.command, list) or not step.command or not all(
            isinstance(argument, str) for argument in step.command
        ):
            raise self._error_factory.create(
                f"Step '{step.id}' legacy script 'command' must be a non-empty list of strings"
            )
        if step.executor is not None or step.args is not None:
            raise self._error_factory.create(
                f"Step '{step.id}' legacy script 'command' must not mix with 'executor' or 'args'"
            )

    def _validate_executor(self, step: ScriptStepFieldReading) -> None:
        if step.executor is not None and (
            not isinstance(step.executor, str) or not step.executor
        ):
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'script' and 'executor' must be a non-empty string"
            )
