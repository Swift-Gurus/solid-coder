"""Restores one workflow input binding from a durable snapshot."""

from collections.abc import Mapping

from harness.flow_validation_error import FlowValidationError
from harness.workflow_input_binding import WorkflowInputBinding
from harness.workflow_input_binding_snapshot_parsing import (
    WorkflowInputBindingSnapshotParsing,
)
from harness.workflow_expression_parsing import WorkflowExpressionParsing


"""
solid-name: WorkflowInputBindingSnapshotParser
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Restores a validated child input binding from a workflow snapshot.
"""
class WorkflowInputBindingSnapshotParser(WorkflowInputBindingSnapshotParsing):
    def __init__(self, expression_parser: WorkflowExpressionParsing) -> None:
        self._expression_parser = expression_parser

    def parse(self, raw: object, alias: str) -> WorkflowInputBinding:
        if not isinstance(raw, Mapping):
            raise FlowValidationError(
                f"Workflow snapshot alias group '{alias}' has invalid input bindings"
            )
        name = raw.get("name")
        expression = raw.get("expression")
        if not isinstance(name, str):
            raise FlowValidationError(
                f"Workflow snapshot alias group '{alias}' has invalid input bindings"
            )
        return WorkflowInputBinding(
            name=name,
            expression=self._expression_parser.parse(expression),
        )
