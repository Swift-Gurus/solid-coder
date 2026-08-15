"""Initializes durable workflow run directories."""

from __future__ import annotations

from pathlib import Path

from harness.models import FlowDef
from harness.workflow_persisting import WorkflowPersisting


"""
solid-name: RunDirectoryScaffolder
solid-category: service
solid-spec: [SPEC-031, SPEC-037]
solid-description: Initializes run directories and persists their resolved workflow snapshots.
"""
class RunDirectoryScaffolder:

    def __init__(self, workflow_persister: WorkflowPersisting) -> None:
        self._workflow_persister = workflow_persister

    def scaffold(self, base_dir: Path, run_id: str, flow_def: FlowDef) -> Path:
        run_dir = base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        self._workflow_persister.persist(run_dir, flow_def)
        return run_dir
