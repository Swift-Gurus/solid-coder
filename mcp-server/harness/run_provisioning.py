"""
solid-name: RunProvisioning
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for allocating a run's identity, directory, and starting metadata.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.models import FlowDef
from harness.run_init import RunInit


class RunProvisioning(Protocol):

    def provision(self, base_dir: Path, flow_def: FlowDef, params: dict, detected_env: str) -> RunInit: ...