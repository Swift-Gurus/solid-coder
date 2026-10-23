"""Defines a typed reference to projected included-workflow outputs."""

from dataclasses import dataclass, field
from typing import Literal

from harness.workflow_expression import WorkflowExpression

"""
solid-name: WorkflowOutputReference
solid-category: model
solid-spec: [SPEC-056]
solid-description: Identifies one declared output projected across an included workflow alias.
"""


@dataclass(frozen=True)
class WorkflowOutputReference:
    workflow_alias: str
    output_name: str
    kind: Literal["workflow_output"] = field(default="workflow_output", init=False)

    @property
    def expression(self) -> WorkflowExpression:
        return WorkflowExpression(
            f"workflows.{self.workflow_alias}.outputs.{self.output_name}"
        )
