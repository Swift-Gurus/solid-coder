"""Builds externally returned workflow-step results."""

from __future__ import annotations

from harness.models import FlowDef, RunState, StepInstance
from harness.step_result import StepResult
from harness.step_result_building import StepResultBuilding

_DELEGATE_TYPE = "delegate"
_INLINE_EXECUTION = {"mode": "inline"}


"""
solid-name: StepResultBuilder
solid-category: service
solid-spec: [SPEC-031]
solid-description: Synthesizes externally returned workflow-step execution results from definitions and run state.
"""
class StepResultBuilder(StepResultBuilding):

    def build(
        self,
        instances: list[StepInstance],
        flow_def: FlowDef,
        run_state: RunState | None = None,
    ) -> list[StepResult]:
        step_map = {s.id: s for s in flow_def.steps}
        results = []
        for instance in instances:
            step_def = step_map.get(instance.step_id)
            if step_def is not None and step_def.type == _DELEGATE_TYPE:
                execution = {"mode": step_def.mode}
            else:
                execution = _INLINE_EXECUTION
            rejection_reason = None
            if step_def is not None and run_state is not None:
                rejection_reason = run_state.rejection_reasons.get(
                    instance.instance_id
                ) or run_state.rejection_reasons.get(instance.step_id)
            results.append(StepResult(
                step_id=instance.step_id,
                instance_id=instance.instance_id,
                prompt=instance.prompt,
                execution=execution,
                rejection_reason=rejection_reason,
            ))
        return results
