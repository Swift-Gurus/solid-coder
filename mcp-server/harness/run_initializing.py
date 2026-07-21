"""
solid-name: RunInitializing
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for allocating a run identity and its run directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.models import FlowDef
from harness.run_init import RunInit


class RunInitializing(Protocol):

    def initialize(self, base_dir: Path, flow_def: FlowDef) -> RunInit: ...