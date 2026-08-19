"""Defines coalescing of destination source line ranges."""

from typing import Protocol

from source.source_line_range import SourceLineRange


"""
solid-name: SourceLineRangesCoalescing
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for appending destination lines into ordered coalesced source ranges.
"""
class SourceLineRangesCoalescing(Protocol):
    def append(
        self,
        ranges: list[SourceLineRange],
        line: int,
    ) -> list[SourceLineRange]: ...
