"""Builds one complete-file source-search target."""

from pathlib import Path

from findings.review_unit_kind import ReviewUnitKind
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_analysis import SourceAnalysis
from source.source_line_range import SourceLineRange
from source.source_search_target import SourceSearchTarget
from source.source_search_target_terms_resolver import (
    SourceSearchTargetTermsResolver,
)
from source.source_search_targets_building import SourceSearchTargetsBuilding


"""
solid-name: FileSourceSearchTargetsBuilder
solid-category: service
solid-spec: [SPEC-040]
solid-description: Materializes one complete immutable document target with all detected source tags.
"""
class FileSourceSearchTargetsBuilder(SourceSearchTargetsBuilding):
    def __init__(self, terms: SourceSearchTargetTermsResolver) -> None:
        self._terms = terms

    def build(
        self,
        source: ResolvedAnalysisSource,
        analysis: SourceAnalysis,
    ) -> list[SourceSearchTarget]:
        name = Path(source.identity).name
        tags = [detection.tag for detection in analysis.detections]
        return [SourceSearchTarget(
            identity=f"{source.identity}#document",
            source_identity=source.identity,
            unit_identity=f"{source.identity}#document",
            name=name,
            kind=ReviewUnitKind.DOCUMENT,
            span=SourceLineRange(
                start=1,
                end=max(1, len(source.text.splitlines())),
            ),
            code=source.text,
            deterministic_terms=self._terms.resolve(name, tags),
        )]
