"""Resolves UTF-8 source byte offsets to one-based lines."""

from source.analysis.provenance.utf16_source_position_resolver import (
    SourceCoordinateResolving,
)

"""
solid-name: UTF8SourceOffsetLineResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Converts a bounded UTF-8 source byte offset into its one-based line identity.
"""


class UTF8SourceOffsetLineResolver(SourceCoordinateResolving[int, int]):
    def resolve(self, source: str, coordinate: int) -> int:
        encoded = source.encode("utf-8")
        bounded_offset = min(max(coordinate, 0), len(encoded))
        return encoded[:bounded_offset].count(b"\n") + 1
