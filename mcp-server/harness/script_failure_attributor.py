from __future__ import annotations

from harness.models import FlowDef, RunState, StepDef


_DEPENDENCY_VALIDATING_STEP_TYPES = {"script", "command", "operation"}


"""
solid-name: ScriptFailureAttributor
solid-category: service
solid-spec: [SPEC-027, SPEC-037, SPEC-056]
solid-description: Attributes deterministic validation-step failures to the responsible step or completed agent input.
"""
class ScriptFailureAttributor:

    def attribute(self, failed_step: StepDef, run_state: RunState, flow_def: FlowDef) -> str:
        if failed_step.type not in _DEPENDENCY_VALIDATING_STEP_TYPES:
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
