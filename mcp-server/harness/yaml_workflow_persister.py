"""
solid-name: YamlWorkflowPersister
solid-category: service
solid-spec: [SPEC-031]
solid-description: Persists a flow definition to the run directory.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import yaml

from harness.models import FlowDef
from harness.workflow_persisting import WorkflowPersisting


class YamlWorkflowPersister:

    def persist(self, run_dir: Path, flow_def: FlowDef) -> None:
        (run_dir / "workflow.yaml").write_text(yaml.dump(asdict(flow_def), default_flow_style=False))
