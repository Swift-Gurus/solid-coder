"""Defines conversion of one Swift parser item into a source unit."""

from typing import Optional, Protocol

from source.source_unit import SourceUnit


"""
solid-name: SwiftASTItemDecoding
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for converting one supported Swift parser item into typed source-unit metadata.
"""
class SwiftASTItemDecoding(Protocol):
    def decode(self, item: object, source: str) -> Optional[SourceUnit]: ...
