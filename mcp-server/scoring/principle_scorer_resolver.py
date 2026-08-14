"""Resolves configured scorers for named review principles."""

from pathlib import Path
from typing import Callable

from scoring.principle_scorer_resolution import PrincipleScorerResolution
from scoring.principle_scorer_resolving import PrincipleScorerResolving
from scoring.unit_metric_scorer_creating import UnitMetricScorerCreating


"""
solid-name: PrincipleScorerResolver
solid-category: service
solid-description: Resolves one configured typed scorer for a named review principle.
"""
class PrincipleScorerResolver(PrincipleScorerResolving):
    def __init__(
        self,
        refs_root: Path,
        scorer_factory: UnitMetricScorerCreating,
        folder_resolver: Callable[[str, Path], Path],
    ) -> None:
        self._refs_root = refs_root
        self._scorer_factory = scorer_factory
        self._folder_resolver = folder_resolver

    def resolve(self, principle: str) -> PrincipleScorerResolution:
        try:
            folder = self._folder_resolver(principle, self._refs_root)
        except (ValueError, FileNotFoundError) as error:
            return PrincipleScorerResolution(error_message=str(error))
        return PrincipleScorerResolution(
            scorer=self._scorer_factory.make(folder),
            principle_folder=folder,
        )
