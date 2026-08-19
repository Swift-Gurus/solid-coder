"""Resolves UTF-8 source byte offsets to one-based lines."""

from source.source_offset_line_resolving import SourceOffsetLineResolving


"""
solid-name: UTF8SourceOffsetLineResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Converts a bounded UTF-8 source byte offset into its one-based line identity.
"""
class UTF8SourceOffsetLineResolver(SourceOffsetLineResolving):
    def resolve(self, source: str, offset: int) -> int:
        encoded = source.encode("utf-8")
        bounded_offset = min(max(offset, 0), len(encoded))
        return encoded[:bounded_offset].count(b"\n") + 1
