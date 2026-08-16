"""Associates one workflow-step instance with its execution outcome."""

from __future__ import annotations

from dataclasses import dataclass

from harness.models import StepInstance
from harness.step_run_outcome import StepRunOutcome


"""
solid-name: StepInstanceExecution
solid-category: model
solid-spec: [SPEC-037]
solid-description: Carries one workflow-step instance together with its execution outcome.
"""
@dataclass(frozen=True)
class StepInstanceExecution:
    instance: StepInstance
    outcome: StepRunOutcome
