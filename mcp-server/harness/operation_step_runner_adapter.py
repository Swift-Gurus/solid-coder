"""Adapts typed operation execution to the generic engine runner contract."""

from typing import cast

from harness.models import StepDef, StepInstance
from harness.operation_input_supplying import OperationInputSupplying
from harness.operation_step_running import OperationStepRunning
from harness.step_run_outcome import StepRunOutcome
from harness.step_running import StepRunning


"""
solid-name: OperationStepRunnerAdapter
solid-category: adapter
solid-spec: [SPEC-010, SPEC-040]
solid-description: Adapts validated operation step instances to the generic engine runner contract.
"""
class OperationStepRunnerAdapter(StepRunning):
    def __init__(
        self,
        runner: OperationStepRunning,
    ) -> None:
        self._runner = runner

    def run(
        self,
        step_instance: StepInstance,
        step_def: StepDef,
    ) -> StepRunOutcome:
        return self._runner.run(
            cast(OperationInputSupplying, step_instance),
            step_def,
        )
