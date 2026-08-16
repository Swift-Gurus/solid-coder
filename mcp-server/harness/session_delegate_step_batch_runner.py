"""Adapts session-delegate execution to the workflow-step batch contract."""

from __future__ import annotations

from harness.models import StepDef, StepInstance
from harness.session_delegate_batch_running import SessionDelegateBatchRunning
from harness.step_batch_running import StepBatchRunning
from harness.step_instance_execution import StepInstanceExecution


"""
solid-name: SessionDelegateStepBatchRunner
solid-category: adapter
solid-spec: [SPEC-037]
solid-description: Executes a workflow-step batch with concurrent session-delegate semantics.
"""
class SessionDelegateStepBatchRunner(StepBatchRunning):
    def __init__(self, runner: SessionDelegateBatchRunning) -> None:
        self._runner = runner

    def run_batch(
        self,
        instances: list[StepInstance],
        step_def: StepDef,
    ) -> list[StepInstanceExecution]:
        return self._runner.run(instances)
