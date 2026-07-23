"""
solid-name: StepShapeValidator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Validates each step's field set against its declared type.
"""

from __future__ import annotations

from typing import Callable

from harness.models import FlowValidationError
from harness.step_shape_validating import StepShapeValidating


class StepShapeValidator(StepShapeValidating):

    def __init__(self) -> None:
        self._validators: dict[str, Callable[[dict], None]] = {
            "agent": self._validate_agent_step,
            "script": self._validate_script_step,
        }

    def validate(self, steps: list[dict]) -> None:
        for step in steps:
            step_type = step.get("type", "agent")
            validator = self._validators.get(step_type, self._validate_agent_step)
            validator(step)

    def _validate_agent_step(self, step: dict) -> None:
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

    def _validate_script_step(self, step: dict) -> None:
        step_id = step.get("id")
        if not step.get("command"):
            raise FlowValidationError(
                f"Step '{step_id}' is type 'script' and must declare 'command'"
            )
        if step.get("prompt") or step.get("prompt_file"):
            raise FlowValidationError(
                f"Step '{step_id}' is type 'script' and must not declare 'prompt' or 'prompt_file'"
            )