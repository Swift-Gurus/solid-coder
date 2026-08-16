"""Defines execution of ready workflow-step instance batches."""

from __future__ import annotations

from typing import Protocol

from harness.models import StepDef, StepInstance
from harness.step_instance_execution import StepInstanceExecution


"""
solid-name: StepBatchRunning
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for executing ready instances of one workflow step as a correlated batch.
"""
class StepBatchRunning(Protocol):
    def run_batch(
        self,
        instances: list[StepInstance],
        step_def: StepDef,
    ) -> list[StepInstanceExecution]: ...
