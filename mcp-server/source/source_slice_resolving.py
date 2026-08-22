"""Defines immutable source-slice resolution."""

from typing import Protocol


"""
solid-name: SourceSliceResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving exact source content between parser offsets.
"""
class SourceSliceResolving(Protocol):
    def resolve(
        self,
        source: str,
        start_offset: int,
        end_offset: int,
    ) -> str: ...
