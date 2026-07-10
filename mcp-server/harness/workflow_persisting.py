"""
solid-name: WorkflowPersisting
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for persisting a flow definition to a run directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.models import FlowDef


class WorkflowPersisting(Protocol):

    def persist(self, run_dir: Path, flow_def: FlowDef) -> None: ...