"""Resolves semantic document positions into exact UTF-8 byte offsets."""

from source.analysis.provenance.semantic_position import SemanticPosition
from source.analysis.provenance.utf16_source_position_resolver import (
    SourceCoordinateResolving,
)

"""
solid-name: UTF8SemanticOffsetResolver
solid-category: utility
solid-spec: [SPEC-064]
solid-description: Converts UTF-16 document positions into UTF-8 offsets while rejecting split surrogate pairs and out-of-range coordinates.
"""


class UTF8SemanticOffsetResolver(SourceCoordinateResolving[SemanticPosition, int]):
    def resolve(self, source: str, coordinate: SemanticPosition) -> int:
        lines = source.split("\n")
        if coordinate.line >= len(lines):
            raise ValueError("Semantic line is outside the document.")
        encoded = lines[coordinate.line].encode("utf-16-le")
        character_end = coordinate.character * 2
        if character_end > len(encoded):
            raise ValueError("Semantic character is outside the line.")
        prefix = "\n".join(lines[: coordinate.line]) + ("\n" if coordinate.line else "")
        prefix += encoded[:character_end].decode("utf-16-le")
        return len(prefix.encode("utf-8"))
