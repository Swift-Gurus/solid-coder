"""
solid-description: Provides scorers for given principle identifiers.
solid-category: service
solid-tags: [utility, service]
"""

from pathlib import Path
from typing import Callable, Optional, Protocol

from scoring.severity_scorer import SeverityScorer
from scoring.principle_scorer_resolution import PrincipleScorerResolution
from scoring.principle_scorer_resolving import PrincipleScorerResolving
from scoring.unit_metric_scoring import UnitMetricScoring
from rules.principal_folder_resolver import resolve as _resolve_folder_fn


"""
solid-name: UnitScoring
solid-category: abstraction
solid-description: Contract for applying server-authoritative rules to unit measurements through typed and compatibility boundaries.
"""
class UnitScoring(UnitMetricScoring, Protocol):
    def score_unit(self, unit_metrics: dict, metric_id: str) -> dict: ...


"""
solid-name: PrincipleScorerProviding
solid-category: abstraction
solid-description: Contract for providing configured scoring capabilities for named review principles.
"""
class PrincipleScorerProviding(PrincipleScorerResolving, Protocol):
    def scorer_for(self, principle: str) -> tuple: ...


"""
solid-name: PrincipleScorerProvider
solid-category: service
solid-description: Provides configured server-authoritative scoring capabilities for named review principles.
"""
class PrincipleScorerProvider:
    """Resolves a principle folder and constructs a scorer for it.

    project_root is passed to SeverityScorer so ConfigBandsProvider can walk
    from the scored file up to the project root, discovering .solid-coder/
    severity-bands.yml overrides along the way. When omitted, ProjectRootFinder
    auto-detects the root from the scored file's path.
    """

    def __init__(
        self,
        refs_root: Path,
        scorer_factory: Optional[Callable[[Path], UnitScoring]] = None,
        folder_resolver: Optional[Callable[[str, Path], Path]] = None,
        project_root: Optional[str] = None,
    ) -> None:
        self._refs_root = refs_root
        self._folder_resolver = folder_resolver or _resolve_folder_fn
        self._scorer_factory = scorer_factory or (
            lambda folder: SeverityScorer.from_folder(folder, project_root=project_root or None)
        )

    def scorer_for(self, principle: str) -> tuple:
        resolution = self.resolve(principle)
        error = None
        if resolution.error_message is not None:
            error = {"error": resolution.error_message}
        return resolution.scorer, error, resolution.principle_folder

    def resolve(self, principle: str) -> PrincipleScorerResolution:
        try:
            folder = self._folder_resolver(principle, self._refs_root)
        except (ValueError, FileNotFoundError) as exc:
            return PrincipleScorerResolution(error_message=str(exc))
        return PrincipleScorerResolution(
            scorer=self._scorer_factory(folder),
            principle_folder=folder,
        )
