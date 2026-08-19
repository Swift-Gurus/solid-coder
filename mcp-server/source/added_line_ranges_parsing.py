"""Defines destination-line extraction from unified diffs."""

from typing import Protocol

from source.source_line_range import SourceLineRange


"""
solid-name: AddedLineRangesParsing
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for extracting coalesced destination-coordinate added ranges from a unified diff.
"""
class AddedLineRangesParsing(Protocol):
    def parse(self, diff: str) -> list[SourceLineRange]: ...
