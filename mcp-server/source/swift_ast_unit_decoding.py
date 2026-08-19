"""Defines decoding of Swift parser JSON into typed source units."""

from typing import Protocol

from source.source_unit import SourceUnit


"""
solid-name: SwiftASTUnitDecoding
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for decoding external Swift parser JSON directly into ordered typed source units.
"""
class SwiftASTUnitDecoding(Protocol):
    def decode(self, parser_json: str, source: str) -> list[SourceUnit]: ...
