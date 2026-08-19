"""Rewrites typed operation steps into public workflow YAML fields."""

from harness.step_def import StepDef
from harness.step_snapshot_rewriting import StepSnapshotRewriting
from harness.workflow_expression_serializing import WorkflowExpressionSerializing


"""
solid-name: OperationStepSnapshotRewriter
solid-category: boundary
solid-spec: [SPEC-031, SPEC-040]
solid-description: Serializes typed logical operations and input bindings into durable public YAML fields.
"""
class OperationStepSnapshotRewriter(StepSnapshotRewriting):
    def __init__(
        self,
        expression_serializer: WorkflowExpressionSerializing,
    ) -> None:
        self._expression_serializer = expression_serializer

    def rewrite(self, snapshot: dict, step: StepDef) -> None:
        snapshot.pop("operation", None)
        if step.operation is None:
            return
        snapshot.pop("outputs", None)
        snapshot["operation"] = step.operation.name
        snapshot["with"] = {
            binding.name: self._expression_serializer.serialize(
                binding.expression
            )
            for binding in step.operation.input_bindings
        }
