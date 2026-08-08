"""
solid-name: RunProvisioning
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for provisioning a run from a flow definition and configuration parameters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.models import FlowDef
from harness.run_init import RunInit


class RunProvisioning(Protocol):

    def provision(self, base_dir: Path, flow_def: FlowDef, params: dict, self_contained: bool = False) -> RunInit: ...
