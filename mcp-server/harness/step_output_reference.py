"""Defines a typed reference to one workflow step output."""

from dataclasses import dataclass

from harness.workflow_expression import WorkflowExpression

"""
solid-name: StepOutputReference
solid-category: model
solid-spec: [SPEC-030, SPEC-037]
solid-description: Identifies one local workflow step and one declared output selected by an authored expression.
"""


@dataclass(frozen=True)
class StepOutputReference:
    step_id: str
    output_name: str

    @property
    def expression(self) -> WorkflowExpression:
        return WorkflowExpression(f"steps.{self.step_id}.outputs.{self.output_name}")
