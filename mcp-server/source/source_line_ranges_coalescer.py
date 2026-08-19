"""Coalesces ordered destination source lines into ranges."""

from source.source_line_range import SourceLineRange
from source.source_line_ranges_coalescing import SourceLineRangesCoalescing


"""
solid-name: SourceLineRangesCoalescer
solid-category: service
solid-spec: [SPEC-040]
solid-description: Appends destination lines into immutable ordered coalesced source ranges.
"""
class SourceLineRangesCoalescer(SourceLineRangesCoalescing):
    def append(
        self,
        ranges: list[SourceLineRange],
        line: int,
    ) -> list[SourceLineRange]:
        if not ranges or ranges[-1].end + 1 != line:
            return [*ranges, SourceLineRange(start=line, end=line)]
        return [
            *ranges[:-1],
            SourceLineRange(start=ranges[-1].start, end=line),
        ]
