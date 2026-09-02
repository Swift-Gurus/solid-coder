"""Defines model-facing rendering of one ready batch group."""

from typing import Protocol

from harness.step_result import StepResult


"""
solid-name: BatchStepRendering
solid-category: abstraction
solid-spec: [SPEC-042]
solid-description: Contract for rendering one shared instruction and its domain-labeled ready items.
"""
class BatchStepRendering(Protocol):
    def render(self, steps: list[StepResult]) -> str: ...
