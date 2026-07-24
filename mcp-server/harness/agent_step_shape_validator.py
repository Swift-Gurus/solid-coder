"""
solid-name: AgentStepShapeValidator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Validates the field set of an agent-type step.
"""

from __future__ import annotations

from harness.models import FlowValidationError
from harness.step_field_validating import StepFieldValidating


class AgentStepShapeValidator(StepFieldValidating):

    def validate(self, step: dict) -> None:
        step_id = step.get("id")
        has_prompt = bool(step.get("prompt"))
        has_prompt_file = bool(step.get("prompt_file"))
        if has_prompt == has_prompt_file:
            raise FlowValidationError(
                f"Step '{step_id}' must declare exactly one of 'prompt' or 'prompt_file'"
            )
        if step.get("command"):
            raise FlowValidationError(
                f"Step '{step_id}' is type 'agent' and must not declare 'command'"
            )