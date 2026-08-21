"""Defines validation of one workflow iteration target."""

from __future__ import annotations

from typing import Protocol

from harness.for_each_validation_target import ForEachValidationTarget
from harness.models import StepDef


"""
solid-name: ForEachTargetValidating
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-037]
solid-description: Contract for validating one workflow entry's iteration source.
"""
class ForEachTargetValidating(Protocol):
    def validate(
        self,
        target: ForEachValidationTarget,
        steps: list[StepDef],
    ) -> None: ...
