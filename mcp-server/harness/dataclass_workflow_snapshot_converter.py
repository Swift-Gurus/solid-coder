"""Adapts workflow dataclasses into serializable snapshot values."""

from __future__ import annotations

from dataclasses import asdict

from harness.flow_def import FlowDef
from harness.workflow_snapshot_converting import WorkflowSnapshotConverting


"""
solid-name: DataclassWorkflowSnapshotConverter
solid-category: adapter
solid-spec: [SPEC-031]
solid-description: Converts typed workflow models into recursively expanded snapshot values.
"""
class DataclassWorkflowSnapshotConverter(WorkflowSnapshotConverting):
    def convert(self, flow_def: FlowDef) -> dict[str, object]:
        return asdict(flow_def)
