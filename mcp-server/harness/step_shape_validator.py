"""
solid-name: StepShapeValidator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Validates each step using the appropriate validator for its type.
"""

from __future__ import annotations

from harness.step_field_validating import StepFieldValidating
from harness.step_shape_validating import StepShapeValidating


class StepShapeValidator(StepShapeValidating):

    def __init__(self, validators: dict[str, StepFieldValidating], default: StepFieldValidating) -> None:
        self._validators = validators
        self._default = default

    def validate(self, steps: list[dict]) -> None:
        for step in steps:
            step_type = step.get("type", "agent")
            validator = self._validators.get(step_type, self._default)
            validator.validate(step)
