"""Resolves source evidence from parser offsets."""

from source.source_evidence import SourceEvidence
from source.source_line_range import SourceLineRange
from source.analysis.provenance.utf16_source_position_resolver import SourceCoordinateResolving


"""
solid-name: SourceEvidenceResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Resolves auditable source evidence spans from parsed source offsets.
"""
class SourceEvidenceResolver:

    def __init__(self, line_resolver: SourceCoordinateResolving[int, int]) -> None:
        self._line_resolver = line_resolver

    def resolve(
        self,
        fact: str,
        source: str,
        start_offset: int,
        end_offset: int,
    ) -> SourceEvidence:
        return SourceEvidence(
            fact=fact,
            span=SourceLineRange(
                start=self._line_resolver.resolve(source, start_offset),
                end=self._line_resolver.resolve(source, end_offset),
            ),
        )
