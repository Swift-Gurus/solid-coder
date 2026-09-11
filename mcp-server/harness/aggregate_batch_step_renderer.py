"""Renders an aggregate batch as one model-facing workflow turn."""

from harness.aggregate_assignment_collecting import AggregateAssignmentCollecting
from harness.aggregate_turn_compiler import AggregateTurnCompiler
from harness.batch_step_rendering import BatchStepRendering
from harness.step_result import StepResult
from json_serializer import JsonSerializing


"""
solid-name: AggregateBatchStepRenderer
solid-category: service
solid-spec: [SPEC-045]
solid-description: Renders original aggregate step results as one compact prompt with an exact submission schema.
"""
class AggregateBatchStepRenderer(BatchStepRendering):
    def __init__(
        self,
        assignments: AggregateAssignmentCollecting,
        compiler: AggregateTurnCompiler,
        json_serializer: JsonSerializing,
    ) -> None:
        self._assignments = assignments
        self._compiler = compiler
        self._json_serializer = json_serializer

    def render(self, steps: list[StepResult]) -> str:
        compiled = self._compiler.compile(self._assignments.collect(steps))
        return (
            f"{compiled.prompt}\n\n"
            "Call flow_next with one JSON object matching this schema. "
            "Do not include undeclared keys:\n"
            f"{self._json_serializer.serialize(compiled.schema)}"
        )
