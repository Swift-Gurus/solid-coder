"""Resolves parsed searchable units from repository snapshots."""

from source.repository_source_snapshot import RepositorySourceSnapshot
from source.repository_source_unit import RepositorySourceUnit
from source.repository_source_unit_projecting import (
    RepositorySourceUnitProjecting,
)
from source.repository_source_units_resolving import (
    RepositorySourceUnitsResolving,
)
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.resolved_source_analyzing import ResolvedSourceAnalyzing
from source.source_frontmatter_reading import SourceFrontmatterReading


"""
solid-name: AnalyzedRepositorySourceUnitsResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Resolves independently searchable parsed units from immutable repository snapshots.
"""
class AnalyzedRepositorySourceUnitsResolver(RepositorySourceUnitsResolving):
    def __init__(
        self,
        analyzer: ResolvedSourceAnalyzing,
        frontmatter_reader: SourceFrontmatterReading,
        projector: RepositorySourceUnitProjecting,
    ) -> None:
        self._analyzer = analyzer
        self._frontmatter_reader = frontmatter_reader
        self._projector = projector

    def resolve(
        self,
        snapshot: RepositorySourceSnapshot,
    ) -> list[RepositorySourceUnit]:
        analysis = self._analyzer.analyze(ResolvedAnalysisSource(
            identity=snapshot.source_identity,
            file_extension=snapshot.path.suffix.casefold(),
            text=snapshot.content,
        ))
        frontmatters = self._frontmatter_reader.read(snapshot.content)
        return [
            self._projector.project(snapshot, unit, frontmatters)
            for unit in analysis.units
        ]
