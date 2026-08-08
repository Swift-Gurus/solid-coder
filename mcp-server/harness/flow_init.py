"""
solid-name: FlowInit
solid-category: model
solid-spec: [SPEC-031]
solid-description: Encapsulates everything a newly initialized flow run needs before its first step executes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from harness.active_run_location import ActiveRunLocation
from harness.models import FlowDef


@dataclass(frozen=True)
class FlowInit:
    location: ActiveRunLocation
    effective_base_dir: Path
    flow_def: FlowDef
