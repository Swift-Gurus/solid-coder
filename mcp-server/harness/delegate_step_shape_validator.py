"""
solid-name: DelegateStepShapeValidator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Validates field constraints for a delegate-type step.
"""

from __future__ import annotations

from harness.models import FlowValidationError
from harness.step_field_validating import StepFieldValidating

_VALID_MODES = {"subagent", "session"}


class DelegateStepShapeValidator(StepFieldValidating):

    def validate(self, step: dict) -> None:
        step_id = step.get("id")
        if not step.get("prompt"):
            raise FlowValidationError(
                f"Step '{step_id}' is type 'delegate' and must declare 'prompt'"
            )
        if step.get("command"):
            raise FlowValidationError(
                f"Step '{step_id}' is type 'delegate' and must not declare 'command'"
            )
        mode = step.get("mode")
        if mode not in _VALID_MODES:
            raise FlowValidationError(
                f"Step '{step_id}' is type 'delegate' and must declare 'mode' as one of {sorted(_VALID_MODES)}"
            )
