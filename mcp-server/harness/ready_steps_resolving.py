"""
solid-description: Contract for determining which step results are ready to return.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Protocol

from harness.models import FlowDef
from harness.step_result import StepResult


class ReadyStepsResolving(Protocol):
    """
    solid-description: Contract for determining which step results are ready given current flow state.
    solid-category: abstraction
    """

    def resolve(self, events_path: str, flow_def: FlowDef, params: dict, detected_env: str) -> list[StepResult]: ...
