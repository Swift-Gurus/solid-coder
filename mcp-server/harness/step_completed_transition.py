"""Applies a step-completed event to reconstructed state."""

from harness.step_completed_event import StepCompletedEvent
from harness.step_instance_completion import StepInstanceCompletion
from harness.step_instance_output_aggregating import StepInstanceOutputAggregating
from harness.step_outputs_building import StepOutputsBuilding


"""
solid-name: StepCompletedTransition
solid-category: service
solid-spec: [SPEC-030]
solid-description: Records validated step outputs and removes the completed step from active execution.
"""
class StepCompletedTransition:

    def __init__(
        self,
        step_outputs_builder: StepOutputsBuilding,
        output_aggregator: StepInstanceOutputAggregating,
    ) -> None:
        self._step_outputs_builder = step_outputs_builder
        self._output_aggregator = output_aggregator

    def apply(self, state: dict, event: dict) -> None:
        completion_event = StepCompletedEvent.model_validate(event)
        step_id = completion_event.step_id or completion_event.instance_id
        outputs = self._step_outputs_builder.build(completion_event.outputs)

        if completion_event.iteration_index is None:
            state["completed"][step_id] = outputs
        else:
            completed_instances = state.setdefault("completed_instances", {})
            completed_instances[completion_event.instance_id] = StepInstanceCompletion(
                step_id=step_id,
                instance_id=completion_event.instance_id,
                iteration_index=completion_event.iteration_index,
                item=completion_event.item,
                outputs=outputs,
            )
            if completion_event.parent_completed:
                matching_completions = [
                    completion
                    for completion in completed_instances.values()
                    if completion.step_id == step_id
                ]
                state["completed"][step_id] = (
                    outputs
                    if completion_event.empty_collection
                    else self._output_aggregator.aggregate(matching_completions)
                )

        if step_id in state["running"]:
            state["running"].remove(step_id)
