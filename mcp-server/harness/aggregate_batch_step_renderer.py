"""Renders an aggregate batch as one model-facing workflow turn."""

from harness.aggregate_assignment_collecting import AggregateAssignmentCollecting
from harness.aggregate_submission_instruction_rendering import (
    AggregateSubmissionInstructionRendering,
)
from harness.aggregate_turn_compiler import AggregateTurnCompiler
from harness.batch_step_rendering import BatchStepRendering
from harness.step_result import StepResult
from json_serializer import JsonSerializing


"""
solid-name: AggregateBatchStepRenderer
solid-category: service
solid-spec: [SPEC-045, SPEC-052]
solid-description: Renders aggregate work with its exact response and correction contract.
"""
class AggregateBatchStepRenderer(BatchStepRendering):
    def __init__(
        self,
        assignments: AggregateAssignmentCollecting,
        compiler: AggregateTurnCompiler,
        submission_instructions: AggregateSubmissionInstructionRendering,
        json_serializer: JsonSerializing,
    ) -> None:
        self._assignments = assignments
        self._compiler = compiler
        self._submission_instructions = submission_instructions
        self._json_serializer = json_serializer

    def render(self, steps: list[StepResult]) -> str:
        assignments = self._assignments.collect(steps)
        compiled = self._compiler.compile(assignments)
        return (
            f"{compiled.prompt}\n\n"
            f"{self._submission_instructions.render(assignments)}\n"
            f"{self._json_serializer.serialize(compiled.schema)}"
        )
