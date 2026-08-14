"""
solid-description: Determines which workflow steps are ready to execute based on their dependencies and run state.
solid-category: service
"""

from __future__ import annotations

from typing import Any

from harness.dag_running import DAGRunning
from harness.models import FlowDef, RunState, StepInstance
from harness.step_instance_expanding import StepInstanceExpanding
from harness.step_readiness_checking import StepReadinessChecking


"""
solid-name: DAGRunner
solid-description: Coordinates workflow-step readiness and runtime instance expansion.
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
"""
class DAGRunner(DAGRunning):

    def __init__(
        self,
        readiness_checker: StepReadinessChecking,
        instance_expander: StepInstanceExpanding,
    ) -> None:
        self._readiness_checker = readiness_checker
        self._instance_expander = instance_expander

    def ready_steps(self, flow_def: FlowDef, run_state: RunState, context: dict[str, Any]) -> list[StepInstance]:
        if run_state.turn_count >= flow_def.max_turns:
            return []
        return [
            instance
            for step in flow_def.steps
            if not self._readiness_checker.is_done_or_running(step.id, run_state)
            and self._readiness_checker.dependencies_met(step, run_state)
            for instance in self._instance_expander.expand(step, context, run_state)
        ]
