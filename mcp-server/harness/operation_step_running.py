"""Defines execution of a typed operation step instance."""

from typing import Protocol

from harness.models import StepDef
from harness.operation_input_supplying import OperationInputSupplying
from harness.step_run_outcome import StepRunOutcome


"""
solid-name: OperationStepRunning
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-040]
solid-description: Contract for executing a workflow instance that supplies resolved operation inputs.
"""
class OperationStepRunning(Protocol):
    def run(
        self,
        step_instance: OperationInputSupplying,
        step_def: StepDef,
    ) -> StepRunOutcome: ...
