"""
solid-name: RunMetadataPersisting
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for persisting and retrieving run metadata across execution steps.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.run_metadata import RunMetadata


class RunMetadataPersisting(Protocol):

    def write(self, run_dir: Path, metadata: RunMetadata) -> None: ...

    def read(self, run_dir: Path) -> RunMetadata: ...
