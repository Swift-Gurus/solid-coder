"""
solid-description: Provides scorers for given principle identifiers, with optional project root for config discovery.
solid-category: service
solid-tags: [utility, service]
"""

import os
from pathlib import Path
from typing import Callable, Optional, Protocol

from scoring.severity_scorer import SeverityScorer
from rules.principal_folder_resolver import resolve as _resolve_folder_fn


class UnitScoring(Protocol):
    def score_unit(self, unit_metrics: dict, metric_id: str) -> dict: ...


class PrincipleScorerProviding(Protocol):
    def scorer_for(self, principle: str) -> tuple: ...


class PrincipleScorerProvider:
    """Resolves a principle folder and constructs a scorer for it.

    project_root is passed to SeverityScorer so ConfigBandsProvider can walk
    from the scored file up to the project root, discovering .solid-coder.yml
    overrides along the way. Defaults to CLAUDE_PROJECT_DIR env var when unset.
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
        resolved_root = project_root or os.environ.get("CLAUDE_PROJECT_DIR", "")
        self._scorer_factory = scorer_factory or (
            lambda folder: SeverityScorer.from_folder(folder, project_root=resolved_root or None)
        )

    def scorer_for(self, principle: str) -> tuple:
        try:
            folder = self._folder_resolver(principle, self._refs_root)
        except (ValueError, FileNotFoundError) as exc:
            return None, {"error": str(exc)}, None
        return self._scorer_factory(folder), None, folder
