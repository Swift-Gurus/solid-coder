"""Defines lookup of completed outputs for one workflow step."""

from typing import Protocol

from harness.run_state import RunState
from harness.step_outputs import StepOutputs


"""
solid-name: CompletedStepOutputsResolving
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for resolving the required completed outputs of one workflow step.
"""
class CompletedStepOutputsResolving(Protocol):
    def resolve(
        self,
        step_id: str,
        run_state: RunState,
    ) -> StepOutputs: ...
