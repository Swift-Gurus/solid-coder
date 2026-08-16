"""Adapts single-instance step execution to the batch contract."""

from __future__ import annotations

from harness.models import StepDef, StepInstance
from harness.step_batch_running import StepBatchRunning
from harness.step_instance_execution import StepInstanceExecution
from harness.step_running import StepRunning


"""
solid-name: SingleInstanceStepBatchRunner
solid-category: adapter
solid-spec: [SPEC-037]
solid-description: Executes a workflow-step batch with single-instance semantics.
"""
class SingleInstanceStepBatchRunner(StepBatchRunning):
    def __init__(self, runner: StepRunning) -> None:
        self._runner = runner

    def run_batch(
        self,
        instances: list[StepInstance],
        step_def: StepDef,
    ) -> list[StepInstanceExecution]:
        if not instances:
            return []
        instance = instances[0]
        return [
            StepInstanceExecution(
                instance=instance,
                outcome=self._runner.run(instance, step_def),
            )
        ]
