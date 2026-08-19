"""Resolves readable source content as one document unit."""

from pathlib import Path

from findings.review_unit_kind import ReviewUnitKind
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_line_range import SourceLineRange
from source.source_unit import SourceUnit


"""
solid-name: WholeDocumentUnitResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Represents readable source content as one deterministic document unit with a complete span.
"""
class WholeDocumentUnitResolver:

    def resolve(self, source: ResolvedAnalysisSource) -> SourceUnit:
        line_count = max(1, len(source.text.splitlines()))
        return SourceUnit(
            identity=f"{source.identity}#document",
            kind=ReviewUnitKind.DOCUMENT,
            name=Path(source.identity).name,
            span=SourceLineRange(start=1, end=line_count),
            start_offset=0,
            end_offset=len(source.text.encode("utf-8")),
        )
