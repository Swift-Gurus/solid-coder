"""Defines selection of ready steps sharing one batch presentation group."""

from typing import Protocol

from harness.step_result import StepResult


"""
solid-name: SiblingBatchStepSelecting
solid-category: abstraction
solid-spec: [SPEC-042]
solid-description: Contract for selecting ready result items that share the first selected item's typed batch identity.
"""
class SiblingBatchStepSelecting(Protocol):
    def select(
        self,
        selected: StepResult,
        steps: list[StepResult],
    ) -> list[StepResult]: ...
