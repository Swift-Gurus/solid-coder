"""Coordinates durable YAML serialization of resolved workflows."""

from __future__ import annotations

from harness.condition_field_rewriting import ConditionFieldRewriting
from harness.flow_def import FlowDef
from harness.rule_step_snapshot_rewriting import RuleStepSnapshotRewriting
from harness.workflow_snapshot_converting import WorkflowSnapshotConverting
from harness.workflow_yaml_serializing import WorkflowYamlSerializing
from harness.yaml_dumping import YamlDumping


"""
solid-name: WorkflowYamlSerializer
solid-category: boundary
solid-spec: [SPEC-031, SPEC-037, SPEC-039]
solid-description: Coordinates conversion of resolved workflows into durable YAML snapshots.
"""
class WorkflowYamlSerializer(WorkflowYamlSerializing):

    def __init__(
        self,
        snapshot_converter: WorkflowSnapshotConverting,
        condition_field_rewriter: ConditionFieldRewriting,
        rule_step_rewriter: RuleStepSnapshotRewriting,
        yaml_dumper: YamlDumping,
    ) -> None:
        self._snapshot_converter = snapshot_converter
        self._condition_field_rewriter = condition_field_rewriter
        self._rule_step_rewriter = rule_step_rewriter
        self._yaml_dumper = yaml_dumper

    def serialize(self, flow_def: FlowDef) -> str:
        snapshot = self._snapshot_converter.convert(flow_def)
        self._condition_field_rewriter.rewrite(snapshot, flow_def.condition)

        serialized_steps = snapshot["steps"]
        for index in range(len(flow_def.steps)):
            self._rule_step_rewriter.rewrite(
                serialized_steps[index],
                flow_def.steps[index],
            )
            self._condition_field_rewriter.rewrite(
                serialized_steps[index],
                flow_def.steps[index].condition,
            )

        return self._yaml_dumper.dump(snapshot)
