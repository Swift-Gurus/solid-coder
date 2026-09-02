"""Defines model-facing rendering of one domain-labeled batch item."""

from typing import Protocol

from harness.step_result import StepResult


"""
solid-name: BatchStepItemRendering
solid-category: abstraction
solid-spec: [SPEC-042]
solid-description: Contract for rendering one domain-labeled batch item and its optional retry guidance.
"""
class BatchStepItemRendering(Protocol):
    def render(self, step: StepResult) -> str: ...
