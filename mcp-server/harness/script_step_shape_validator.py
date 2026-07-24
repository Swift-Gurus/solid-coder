"""
solid-name: ScriptStepShapeValidator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Validates the field set of a script-type step.
"""

from __future__ import annotations

from harness.models import FlowValidationError
from harness.step_field_validating import StepFieldValidating


class ScriptStepShapeValidator(StepFieldValidating):

    def validate(self, step: dict) -> None:
        step_id = step.get("id")
        if not step.get("command"):
            raise FlowValidationError(
                f"Step '{step_id}' is type 'script' and must declare 'command'"
            )
        if step.get("prompt") or step.get("prompt_file"):
            raise FlowValidationError(
                f"Step '{step_id}' is type 'script' and must not declare 'prompt' or 'prompt_file'"
            )
