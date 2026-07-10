"""
solid-name: StepResultBuilding
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for building step results from step instances.
"""

from __future__ import annotations

from typing import Protocol

from harness.models import FlowDef, StepInstance
from harness.step_result import StepResult


class StepResultBuilding(Protocol):

    def build(self, instances: list[StepInstance], flow_def: FlowDef, detected_env: str) -> list[StepResult]: ...
