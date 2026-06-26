""" 
solid-description: Contract for determining which workflow steps are ready to execute.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Any, Protocol

from harness.models import FlowDef, RunState, StepInstance


class DAGRunning(Protocol):
    """
    solid-description: Contract for determining which steps are ready to execute given a flow definition and current execution state.
    solid-category: abstraction
    """

    def ready_steps(self, flow_def: FlowDef, run_state: RunState, context: dict[str, Any]) -> list[StepInstance]: ...