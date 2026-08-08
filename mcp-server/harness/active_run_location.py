"""
solid-name: ActiveRunLocation
solid-category: model
solid-spec: [SPEC-031]
solid-description: Filesystem locations for the currently active run.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ActiveRunLocation:
    run_id: str
    base_dir: Path
    run_dir: Path
    events_path: str
    workflow_path: str