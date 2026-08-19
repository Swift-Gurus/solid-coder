"""Defines complete readable-file range resolution."""

from pathlib import Path
from typing import Protocol

from source.source_line_range import SourceLineRange


"""
solid-name: WholeFileRangeResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving the complete inclusive line range of a readable project file.
"""
class WholeFileRangeResolving(Protocol):
    def resolve(self, path: Path) -> list[SourceLineRange]: ...
