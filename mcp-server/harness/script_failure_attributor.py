from __future__ import annotations

from harness.models import FlowDef, RunState, StepDef


_PROCESS_STEP_TYPES = {"script", "command"}


"""
solid-name: ScriptFailureAttributor
solid-category: service
solid-spec: [SPEC-027, SPEC-037]
solid-description: Attributes process-step failures to the responsible process step or completed agent input.
"""
class ScriptFailureAttributor:

    def attribute(self, failed_step: StepDef, run_state: RunState, flow_def: FlowDef) -> str:
        if failed_step.type not in _PROCESS_STEP_TYPES:
            return failed_step.id
        step_map = {step.id: step for step in flow_def.steps}
        candidates = [
            dep for dep in failed_step.depends_on
            if dep in run_state.completed and step_map.get(dep) is not None and step_map[dep].type == "agent"
        ]
        if not candidates:
            return failed_step.id
        completion_order = list(run_state.completed.keys())
        return max(candidates, key=completion_order.index)
