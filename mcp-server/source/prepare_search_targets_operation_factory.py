"""Composes deterministic source-search target preparation."""

from harness.project_context import ProjectDirectoryReading
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
    def make(
        self, project_directory: ProjectDirectoryReading | None = None
    ) -> PrepareSearchTargetsOperation:
        return PrepareSearchTargetsOperation(
            source_resolver=AnalysisSourceResolverFactory().make(project_directory),
            analyzer=ResolvedSourceAnalyzerFactory().make(),
            targets=SourceSearchTargetsBuilderFactory().make(),
        )
