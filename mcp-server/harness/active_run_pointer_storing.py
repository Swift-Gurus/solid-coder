"""
solid-name: ActiveRunPointerStoring
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract that defines atomic read, write (fail-if-exists), and delete operations for the active run identifier.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ActiveRunPointerStoring(Protocol):

    def read(self, base_dir: Path) -> str: ...

    def write(self, base_dir: Path, run_id: str) -> None: ...

    def delete(self, base_dir: Path) -> None: ...