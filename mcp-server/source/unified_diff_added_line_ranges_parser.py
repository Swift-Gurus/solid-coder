"""Extracts destination-coordinate added ranges from unified diffs."""

from source.added_line_ranges_parsing import AddedLineRangesParsing
from source.diff_hunk_destination_decoding import DiffHunkDestinationDecoding
from source.source_line_range import SourceLineRange
from source.source_line_ranges_coalescing import SourceLineRangesCoalescing


"""
solid-name: UnifiedDiffAddedLineRangesParser
solid-category: boundary
solid-spec: [SPEC-040]
solid-description: Parses unified-diff lines into destination-coordinate added source ranges.
"""
class UnifiedDiffAddedLineRangesParser(AddedLineRangesParsing):
    def __init__(
        self,
        destination_decoder: DiffHunkDestinationDecoding,
        ranges: SourceLineRangesCoalescing,
    ) -> None:
        self._destination_decoder = destination_decoder
        self._ranges = ranges

    def parse(self, diff: str) -> list[SourceLineRange]:
        ranges: list[SourceLineRange] = []
        destination_line: int | None = None
        for line in diff.splitlines():
            if line.startswith("@@ "):
                destination_line = self._destination_decoder.decode(line)
                continue
            if destination_line is None:
                continue
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("+"):
                ranges = self._ranges.append(ranges, destination_line)
                destination_line += 1
                continue
            if line.startswith("-") or line.startswith("\\"):
                continue
            destination_line += 1
        return ranges
