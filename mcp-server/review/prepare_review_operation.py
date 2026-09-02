"""Normalizes explicit review targets through deterministic source services."""

from source.analysis_source_resolving import AnalysisSourceResolving
from source.analyze_source_input import AnalyzeSourceInput
from source.resolved_source_analyzing import ResolvedSourceAnalyzing
from source.search_target_granularity import SearchTargetGranularity
from source.source_search_targets_builder import SourceSearchTargetsBuilder
from review.normalized_review_file_builder import NormalizedReviewFileBuilder
from review.normalized_review_input import NormalizedReviewInput
from review.prepare_review_input import PrepareReviewInput


"""
solid-name: PrepareReviewOperation
solid-category: service
solid-spec: [SPEC-041]
solid-description: Normalizes one explicit prospective review buffer by coordinating existing source analysis and target construction capabilities.
"""
class PrepareReviewOperation:
    def __init__(
        self,
        source_resolver: AnalysisSourceResolving,
        analyzer: ResolvedSourceAnalyzing,
        targets: SourceSearchTargetsBuilder,
        review_file: NormalizedReviewFileBuilder,
    ) -> None:
        self._source_resolver = source_resolver
        self._analyzer = analyzer
        self._targets = targets
        self._review_file = review_file

    def execute(
        self,
        operation_input: PrepareReviewInput,
    ) -> NormalizedReviewInput:
        source = self._source_resolver.resolve(
            AnalyzeSourceInput(source=operation_input.target)
        )
        analysis = self._analyzer.analyze(source)
        file_targets = self._targets.build(
            source,
            analysis,
            SearchTargetGranularity.FILE,
        )
        unit_targets = self._targets.build(
            source,
            analysis,
            SearchTargetGranularity.UNIT,
        )
        return self._review_file.build(
            analysis,
            file_targets.targets[0],
            unit_targets.targets,
            file_targets.snapshot,
        )
