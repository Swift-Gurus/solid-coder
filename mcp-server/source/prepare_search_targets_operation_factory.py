"""Composes deterministic source-search target preparation."""

from source.analysis_source_resolver_factory import AnalysisSourceResolverFactory
from source.prepare_search_targets_operation import PrepareSearchTargetsOperation
from source.resolved_source_analyzer_factory import ResolvedSourceAnalyzerFactory
from source.source_search_targets_builder_factory import (
    SourceSearchTargetsBuilderFactory,
)


"""
solid-name: PrepareSearchTargetsOperationFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Provides immutable source resolution, analysis, and typed search-target preparation as one operation.
"""
class PrepareSearchTargetsOperationFactory:
    def make(self) -> PrepareSearchTargetsOperation:
        return PrepareSearchTargetsOperation(
            source_resolver=AnalysisSourceResolverFactory().make(),
            analyzer=ResolvedSourceAnalyzerFactory().make(),
            targets=SourceSearchTargetsBuilderFactory().make(),
        )
