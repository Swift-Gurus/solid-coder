"""
solid-name: StepResultBuilding
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract that defines result synthesis from execution tracking data with flow awareness.
"""

from __future__ import annotations

from typing import Protocol

from harness.models import FlowDef, RunState, StepInstance
from harness.step_result import StepResult


class StepResultBuilding(Protocol):

    def build(
        self,
        instances: list[StepInstance],
        flow_def: FlowDef,
        detected_env: str,
        run_state: RunState | None = None,
    ) -> list[StepResult]: ...
