"""Builds one parsed-unit source-search target."""

from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_analysis import SourceAnalysis
from source.source_search_target import SourceSearchTarget
from source.source_search_target_terms_resolver import (
    SourceSearchTargetTermsResolver,
)
from source.source_unit import SourceUnit
from source.source_unit_search_target_building import (
    SourceUnitSearchTargetBuilding,
)
from source.source_unit_tags_resolving import SourceUnitTagsResolving
from source.utf8_source_slice_resolver import UTF8SourceSliceResolver


"""
solid-name: SourceUnitSearchTargetBuilder
solid-category: service
solid-spec: [SPEC-040]
solid-description: Prepares one searchable source-unit target with immutable code and normalized analysis terms.
"""
class SourceUnitSearchTargetBuilder(SourceUnitSearchTargetBuilding):
    def __init__(
        self,
        tags: SourceUnitTagsResolving,
        terms: SourceSearchTargetTermsResolver,
        source_slice: UTF8SourceSliceResolver,
    ) -> None:
        self._tags = tags
        self._terms = terms
        self._source_slice = source_slice

    def build(
        self,
        source: ResolvedAnalysisSource,
        analysis: SourceAnalysis,
        unit: SourceUnit,
    ) -> SourceSearchTarget:
        return SourceSearchTarget(
            identity=f"{source.identity}#{unit.identity}",
            source_identity=source.identity,
            name=unit.name,
            kind=unit.kind,
            span=unit.span,
            code=self._source_slice.resolve(
                source.text,
                unit.start_offset,
                unit.end_offset,
            ),
            deterministic_terms=self._terms.resolve(
                unit.name,
                self._tags.resolve(analysis.detections, unit.identity),
            ),
        )
