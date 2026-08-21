"""Prepares deterministic source-search targets."""

from source.analysis_source_resolving import AnalysisSourceResolving
from source.analyze_source_input import AnalyzeSourceInput
from source.prepare_search_targets_input import PrepareSearchTargetsInput
from source.prepare_search_targets_output import PrepareSearchTargetsOutput
from source.resolved_source_analyzing import ResolvedSourceAnalyzing
from source.source_search_targets_builder import SourceSearchTargetsBuilder


"""
solid-name: PrepareSearchTargetsOperation
solid-category: service
solid-spec: [SPEC-040]
solid-description: Resolves and analyzes immutable source once before preparing typed file-or-unit search targets.
"""
class PrepareSearchTargetsOperation:
    def __init__(
        self,
        source_resolver: AnalysisSourceResolving,
        analyzer: ResolvedSourceAnalyzing,
        targets: SourceSearchTargetsBuilder,
    ) -> None:
        self._source_resolver = source_resolver
        self._analyzer = analyzer
        self._targets = targets

    def execute(
        self,
        operation_input: PrepareSearchTargetsInput,
    ) -> PrepareSearchTargetsOutput:
        source = self._source_resolver.resolve(
            AnalyzeSourceInput(source=operation_input.source)
        )
        analysis = self._analyzer.analyze(source)
        return self._targets.build(
            source,
            analysis,
            operation_input.granularity,
        )
