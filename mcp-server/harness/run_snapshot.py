"""
solid-name: RunSnapshot
solid-category: model
solid-spec: [SPEC-013]
solid-description: Captures the execution state of a run and the steps ready for processing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.models import RunState, StepInstance


@dataclass(frozen=True)
class RunSnapshot:
    run_state: RunState
    ready: list[StepInstance] = field(default_factory=list)
