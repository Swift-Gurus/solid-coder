"""Composes deterministic review-target normalization."""

from harness.ordered_string_collector import OrderedStringCollector
from harness.rule_applicability_context_resolver import (
    RuleApplicabilityContextResolver,
)
from review.normalized_review_file_builder import NormalizedReviewFileBuilder
from review.prepare_review_operation import PrepareReviewOperation
from source.analysis_source_resolver_factory import AnalysisSourceResolverFactory
from source.resolved_source_analyzer_factory import ResolvedSourceAnalyzerFactory
from source.scoped_technology_detections_resolver import (
    ScopedTechnologyDetectionsResolver,
)
from source.source_search_targets_builder_factory import (
    SourceSearchTargetsBuilderFactory,
)


"""
solid-name: PrepareReviewOperationFactory
solid-category: factory
solid-spec: [SPEC-041]
solid-description: Creates normalized review operations for prospective review inputs.
"""
class PrepareReviewOperationFactory:
    def make(self) -> PrepareReviewOperation:
        return PrepareReviewOperation(
            source_resolver=AnalysisSourceResolverFactory().make(),
            analyzer=ResolvedSourceAnalyzerFactory().make(),
            targets=SourceSearchTargetsBuilderFactory().make(),
            review_file=NormalizedReviewFileBuilder(
                applicability=RuleApplicabilityContextResolver(
                    tag_collector=OrderedStringCollector()
                ),
                evidence=ScopedTechnologyDetectionsResolver(),
            ),
        )
