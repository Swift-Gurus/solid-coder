"""Defines validation of one selected model-facing batch group."""

from typing import Protocol

from harness.step_result import StepResult

"""
solid-name: BatchStepGroupValidating
solid-category: abstraction
solid-spec: [SPEC-042, SPEC-043]
solid-description: Contract for verifying that a selected batch group is valid.
"""


class BatchStepGroupValidating(Protocol):
    def validate(self, steps: list[StepResult]) -> None: ...
