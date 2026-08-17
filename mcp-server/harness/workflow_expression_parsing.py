"""Defines workflow-expression decoding at input boundaries."""

from typing import Protocol

from harness.workflow_expression import WorkflowExpression


"""
solid-name: WorkflowExpressionParsing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for decoding external workflow-expression values into normalized expressions.
"""
class WorkflowExpressionParsing(Protocol):
    def parse(self, raw: object) -> WorkflowExpression: ...
