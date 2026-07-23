"""
solid-name: StepRunning
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for executing a step to produce a run outcome.
"""

from __future__ import annotations

from typing import Protocol

from harness.models import StepDef, StepInstance
from harness.step_run_outcome import StepRunOutcome


class StepRunning(Protocol):

    def run(self, step_instance: StepInstance, step_def: StepDef) -> StepRunOutcome: ...