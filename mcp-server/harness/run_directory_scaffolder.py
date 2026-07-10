"""
solid-name: RunDirectoryScaffolder
solid-category: service
solid-spec: [SPEC-013]
solid-description: Initializes a run directory for a given run ID and persists the provided flow definition.
"""

from __future__ import annotations

from pathlib import Path

from harness.models import FlowDef
from harness.workflow_persisting import WorkflowPersisting
from harness.yaml_workflow_persister import YamlWorkflowPersister


class RunDirectoryScaffolder:

    def __init__(self, workflow_persister: WorkflowPersisting | None = None) -> None:
        self._workflow_persister: WorkflowPersisting = workflow_persister or YamlWorkflowPersister()

    def scaffold(self, base_dir: Path, run_id: str, flow_def: FlowDef) -> Path:
        run_dir = base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        self._workflow_persister.persist(run_dir, flow_def)
        return run_dir
