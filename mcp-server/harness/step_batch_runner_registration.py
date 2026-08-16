"""Associates a workflow execution identity with its batch runner."""

from __future__ import annotations

from dataclasses import dataclass

from harness.models import StepDef
from harness.step_batch_running import StepBatchRunning


"""
solid-name: StepBatchRunnerRegistration
solid-category: model
solid-spec: [SPEC-037]
solid-description: Associates a workflow step type and execution mode with its batch execution capability.
"""
@dataclass(frozen=True)
class StepBatchRunnerRegistration:
    step_type: str
    mode: str
    runner: StepBatchRunning

    def matches(self, step_def: StepDef) -> bool:
        type_matches = step_def.type == self.step_type
        mode_matches = not self.mode or step_def.mode == self.mode
        return type_matches and mode_matches
