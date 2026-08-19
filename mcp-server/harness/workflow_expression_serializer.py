"""Serializes normalized workflow expressions into public YAML syntax."""

from harness.workflow_expression import WorkflowExpression
from harness.workflow_expression_serializing import WorkflowExpressionSerializing


"""
solid-name: WorkflowExpressionSerializer
solid-category: boundary
solid-spec: [SPEC-037, SPEC-040]
solid-description: Serializes normalized workflow expressions into reversible public YAML values.
"""
class WorkflowExpressionSerializer(WorkflowExpressionSerializing):
    def serialize(self, expression: WorkflowExpression) -> str:
        return f"{{{{{expression.value}}}}}"
