"""
solid-name: RunInit
solid-category: model
solid-spec: [SPEC-013]
solid-description: Encapsulates the unique identifier and working directory of a newly initialized run.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunInit:
    run_id: str
    run_dir: Path
