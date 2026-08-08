"""
solid-name: ActiveRunLocationAssembling
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for assembling an ActiveRunLocation from run identity and directory paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.active_run_location import ActiveRunLocation


class ActiveRunLocationAssembling(Protocol):
    def assemble(self, run_id: str, base_dir: Path, run_dir: Path) -> ActiveRunLocation: ...
