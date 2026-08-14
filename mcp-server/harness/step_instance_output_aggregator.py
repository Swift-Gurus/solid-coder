"""Aggregates completed workflow iteration outputs."""

from __future__ import annotations

from harness.step_instance_completion import StepInstanceCompletion
from harness.step_outputs import StepOutputs


"""
solid-name: StepInstanceOutputAggregator
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Combines ordered workflow iteration results into deterministic parent-step output lists.
"""
class StepInstanceOutputAggregator:
    def aggregate(self, completions: list[StepInstanceCompletion]) -> StepOutputs:
        ordered = sorted(completions, key=lambda completion: completion.iteration_index)
        if not ordered:
            return StepOutputs()

        output_names = ordered[0].outputs.values.keys()
        return StepOutputs(values={
            output_name: [
                completion.outputs.get(output_name)
                for completion in ordered
            ]
            for output_name in output_names
        })
