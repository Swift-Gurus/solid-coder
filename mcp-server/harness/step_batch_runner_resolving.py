"""Defines selection of workflow-step batch execution capabilities."""

from __future__ import annotations

from typing import Protocol

from harness.models import StepDef
from harness.step_batch_running import StepBatchRunning


"""
solid-name: StepBatchRunnerResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for resolving batch execution by workflow step type and mode.
"""
class StepBatchRunnerResolving(Protocol):
    def resolve(self, step_def: StepDef) -> StepBatchRunning: ...
