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
from harness.workflow_yaml_serializer import WorkflowYamlSerializer
from harness.yaml_workflow_persister import YamlWorkflowPersister


def make_workflow_persister() -> WorkflowPersisting:
    return YamlWorkflowPersister(
        workflow_serializer=WorkflowYamlSerializer(
            snapshot_converter=DataclassWorkflowSnapshotConverter(),
            condition_field_rewriter=ConditionFieldRewriter(
                condition_serializer=make_condition_serializer(),
            ),
            step_rewriters=[
                RuleStepSnapshotRewriter(),
                OperationStepSnapshotRewriter(
                    WorkflowExpressionSerializer()
                ),
            ],
            yaml_dumper=SafeYamlDumper(),
        )
    )
