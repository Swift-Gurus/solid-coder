"""Defines added-line discovery for one tracked source path."""

from pathlib import Path
from typing import Protocol

from source.source_line_range import SourceLineRange


"""
solid-name: AddedLineRangesReading
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for reading destination-coordinate added ranges for one tracked source path.
"""
class AddedLineRangesReading(Protocol):
    def read(
        self,
        project_root: Path,
        paths: list[str],
    ) -> list[SourceLineRange]: ...
