"""Defines selection of the next model-facing ready step."""

from __future__ import annotations

from typing import Protocol

from harness.step_result import StepResult


"""
solid-name: ReadyStepSelecting
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for selecting the next queued ready step exposed to a model.
"""
class ReadyStepSelecting(Protocol):
    def select(self, steps: list[StepResult]) -> StepResult | None: ...
