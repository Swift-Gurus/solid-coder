"""Applies a rejected-step event to reconstructed state."""

from harness.run_state_transitioning import RunStateTransitioning


"""
solid-name: StepRejectedTransition
solid-category: service
solid-spec: [SPEC-027]
solid-description: Records a failed attempt and reopens the rejected completed step for another execution.
"""
class StepRejectedTransition:

    def __init__(self, attempt_transition: RunStateTransitioning) -> None:
        self._attempt_transition = attempt_transition

    def apply(self, state: dict, event: dict) -> None:
        self._attempt_transition.apply(state, event)
        step_id = event.get("step_id", "")
        state["completed"].pop(step_id, None)
        completed_instances = state.get("completed_instances", {})
        rejected_instances = [
            completion.instance_id
            for completion in completed_instances.values()
            if completion.step_id == step_id
        ]
        for instance_id in rejected_instances:
            completed_instances.pop(instance_id)
        if "included_workflow_completions" in state:
            state["included_workflow_completions"] = [
                completion
                for completion in state["included_workflow_completions"]
                if completion.execution_step_id != step_id
            ]
        state.get("metric_derivations", {}).pop(step_id, None)
