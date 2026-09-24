"""Assembles durable workflow persistence collaborators."""

from harness.condition_field_rewriter import ConditionFieldRewriter
from harness.condition_serializer_factory import make_condition_serializer
from harness.dataclass_workflow_snapshot_converter import (
    DataclassWorkflowSnapshotConverter,
)
from harness.operation_step_snapshot_rewriter import OperationStepSnapshotRewriter
from harness.safe_yaml_dumper import SafeYamlDumper
from harness.rule_step_snapshot_rewriter import RuleStepSnapshotRewriter
from harness.workflow_persisting import WorkflowPersisting
from harness.workflow_expression_serializer import WorkflowExpressionSerializer
from harness.workflow_output_snapshot_serializer import WorkflowOutputSnapshotSerializer
from harness.workflow_yaml_serializer import WorkflowYamlSerializer
from harness.yaml_workflow_persister import YamlWorkflowPersister


"""
solid-name: WorkflowPersisterFactory
solid-category: service
solid-spec: [SPEC-030, SPEC-037, SPEC-053]
solid-description: Provides durable workflow snapshot persistence.
"""
class WorkflowPersisterFactory:
    def make(self) -> WorkflowPersisting:
        condition_serializer = make_condition_serializer()
        expression_serializer = WorkflowExpressionSerializer()
        return YamlWorkflowPersister(
            workflow_serializer=WorkflowYamlSerializer(
                snapshot_converter=DataclassWorkflowSnapshotConverter(),
                condition_field_rewriter=ConditionFieldRewriter(
                    condition_serializer=condition_serializer,
                ),
                step_rewriters=[
                    RuleStepSnapshotRewriter(
                        condition_serializer=condition_serializer,
                        expression_serializer=expression_serializer,
                    ),
                    OperationStepSnapshotRewriter(
                        expression_serializer
                    ),
                ],
                output_serializer=WorkflowOutputSnapshotSerializer(),
                yaml_dumper=SafeYamlDumper(),
            )
        )
