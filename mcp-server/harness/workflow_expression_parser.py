"""Decodes external workflow-expression values."""

from collections.abc import Mapping

from harness.flow_validation_error import FlowValidationError
from harness.workflow_expression import WorkflowExpression
from harness.workflow_expression_parsing import WorkflowExpressionParsing


"""
solid-name: WorkflowExpressionParser
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Decodes authored and snapshotted workflow expressions into normalized typed values.
"""
class WorkflowExpressionParser(WorkflowExpressionParsing):
    def parse(self, raw: object) -> WorkflowExpression:
        if isinstance(raw, Mapping):
            raw = raw.get("value")
        if not isinstance(raw, str):
            raise FlowValidationError("Workflow expression must be a string")

        normalized = raw.strip()
        has_opening_wrapper = normalized.startswith("{{")
        has_closing_wrapper = normalized.endswith("}}")
        if has_opening_wrapper != has_closing_wrapper:
            raise FlowValidationError("Workflow expression has an incomplete wrapper")
        if has_opening_wrapper:
            normalized = normalized[2:-2].strip()
        if not normalized:
            raise FlowValidationError("Workflow expression must not be empty")
        return WorkflowExpression(value=normalized)
