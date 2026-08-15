"""Persists resolved workflow snapshots in run directories."""

from __future__ import annotations

from pathlib import Path

from harness.models import FlowDef
from harness.workflow_persisting import WorkflowPersisting
from harness.workflow_yaml_serializing import WorkflowYamlSerializing


"""
solid-name: YamlWorkflowPersister
solid-category: service
solid-spec: [SPEC-031, SPEC-037]
solid-description: Persists durable workflow snapshots in run directories.
"""
class YamlWorkflowPersister:

    def __init__(self, workflow_serializer: WorkflowYamlSerializing) -> None:
        self._workflow_serializer = workflow_serializer

    def persist(self, run_dir: Path, flow_def: FlowDef) -> None:
        (run_dir / "workflow.yaml").write_text(
            self._workflow_serializer.serialize(flow_def)
        )
