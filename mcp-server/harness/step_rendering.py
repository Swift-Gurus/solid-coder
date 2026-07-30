"""
solid-name: StepRendering
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for rendering steps into a string representation.
"""

from __future__ import annotations

from typing import Protocol

from harness.step_result import StepResult


class StepRendering(Protocol):
    def render_steps(self, steps: list[StepResult]) -> str: ...
