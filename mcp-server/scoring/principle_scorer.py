"""
solid-description: Provides scorers for given principle identifiers.
solid-category: service
solid-tags: [utility, service]
"""

from typing import Protocol

from scoring.principle_scorer_resolution import PrincipleScorerResolution
from scoring.principle_scorer_resolving import PrincipleScorerResolving


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
class PrincipleScorerProvider(PrincipleScorerProviding):
    """Resolves a principle folder and constructs a scorer for it.

    project_root is passed to SeverityScorer so ConfigBandsProvider can walk
    from the scored file up to the project root, discovering .solid-coder/
    severity-bands.yml overrides along the way. When omitted, ProjectRootFinder
    auto-detects the root from the scored file's path.
    """

    def __init__(
        self,
        resolver: PrincipleScorerResolving,
    ) -> None:
        self._resolver = resolver

    def scorer_for(self, principle: str) -> tuple:
        resolution = self._resolver.resolve(principle)
        error = None
        if resolution.error_message is not None:
            error = {"error": resolution.error_message}
        return resolution.scorer, error, resolution.principle_folder

    def resolve(self, principle: str) -> PrincipleScorerResolution:
        return self._resolver.resolve(principle)
