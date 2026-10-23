"""Resolves UTF-8 byte offsets to exact semantic document positions."""

from typing import Protocol, TypeVar

from source.analysis.provenance.semantic_position import SemanticPosition

Coordinate_contra = TypeVar("Coordinate_contra", contravariant=True)
ResolvedCoordinate_co = TypeVar("ResolvedCoordinate_co", covariant=True)


"""
solid-name: SourceCoordinateResolving
solid-category: abstraction
solid-spec: [SPEC-040, SPEC-064]
solid-description: Contract for resolving a typed source coordinate against exact document content.
"""


class SourceCoordinateResolving(Protocol[Coordinate_contra, ResolvedCoordinate_co]):
    def resolve(
        self, source: str, coordinate: Coordinate_contra
    ) -> ResolvedCoordinate_co: ...


"""
solid-name: UTF16SourcePositionResolver
solid-category: utility
solid-spec: [SPEC-064]
solid-description: Resolves exact UTF-8 byte offsets into UTF-16 document positions while rejecting split characters and out-of-range offsets.
"""


class UTF16SourcePositionResolver(SourceCoordinateResolving[int, SemanticPosition]):
    def resolve(self, source: str, coordinate: int) -> SemanticPosition:
        encoded = source.encode("utf-8")
        if coordinate < 0 or coordinate > len(encoded):
            raise ValueError("Source byte offset is outside the document.")
        prefix = encoded[:coordinate].decode("utf-8")
        return SemanticPosition(
            line=prefix.count("\n"),
            character=len(prefix.rsplit("\n", 1)[-1].encode("utf-16-le")) // 2,
        )
