"""Defines exact byte loading for one source path."""

from pathlib import Path
from typing import Protocol


"""
solid-name: SourceBytesReading
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for reading the exact bytes of one accessible source path.
"""
class SourceBytesReading(Protocol):
    def read(self, path: Path) -> bytes: ...
