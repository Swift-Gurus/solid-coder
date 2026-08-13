"""Validates the fields of a delegate workflow step."""

from __future__ import annotations

from harness.delegate_step_field_reading import DelegateStepFieldReading
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.step_field_validating import StepFieldValidating

_VALID_MODES = {"subagent", "session"}


"""
solid-name: DelegateStepShapeValidator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Validates prompt, command, and mode fields declared by a delegate workflow step.
"""
class DelegateStepShapeValidator(StepFieldValidating[DelegateStepFieldReading]):
    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def validate(self, step: DelegateStepFieldReading) -> None:
        if not step.prompt:
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'delegate' and must declare 'prompt'"
            )
        if step.command:
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'delegate' and must not declare 'command'"
            )
        if step.mode not in _VALID_MODES:
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'delegate' and must declare 'mode' as one of {sorted(_VALID_MODES)}"
            )
