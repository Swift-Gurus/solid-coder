"""Defines formatting of one model-facing workflow step."""

from typing import Protocol

from harness.step_result import StepResult


"""
solid-name: SingleStepRendering
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for rendering one selected workflow step for a model.
"""
class SingleStepRendering(Protocol):
    def render(self, step: StepResult) -> str: ...
