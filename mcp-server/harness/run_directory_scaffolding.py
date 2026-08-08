"""
solid-name: RunDirectoryScaffolding
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for preparing a run directory that persists the flow definition.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.models import FlowDef


class RunDirectoryScaffolding(Protocol):

    def scaffold(self, base_dir: Path, run_id: str, flow_def: FlowDef) -> Path: ...