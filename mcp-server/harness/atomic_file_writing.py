"""
solid-name: AtomicFileWriting
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for atomically writing content to a file path, failing if the file already exists.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class AtomicFileWriting(Protocol):

    def write_exclusive(self, path: Path, content: bytes) -> None: ...
