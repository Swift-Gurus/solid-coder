"""
solid-name: ScriptFailureAttributor
solid-category: service
solid-spec: [SPEC-027]
solid-description: Identifies the step responsible for a script step failure—either the step itself or an upstream dependency.
"""

from __future__ import annotations

from harness.models import FlowDef, RunState, StepDef


class ScriptFailureAttributor:

    def attribute(self, failed_step: StepDef, run_state: RunState, flow_def: FlowDef) -> str:
        step_map = {step.id: step for step in flow_def.steps}
        candidates = [
            dep for dep in failed_step.depends_on
            if dep in run_state.completed and step_map.get(dep) is not None and step_map[dep].type == "agent"
        ]
        if not candidates:
            return failed_step.id
        completion_order = list(run_state.completed.keys())
        return max(candidates, key=completion_order.index)
