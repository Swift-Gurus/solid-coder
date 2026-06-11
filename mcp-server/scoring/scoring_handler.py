"""solid-description: Service that enriches batch analysis outputs with file severity scores.
solid-category: service
solid-tags: [utility, service]
"""

from typing import Any, Optional, Protocol

from scoring.files_scoring_handler import FilesScoringCapable
from scoring.principle_scorer import PrincipleScorerProviding


class ScoringHandling(Protocol):
    def score_severity(self, partial_outputs: list) -> dict: ...
    def submit_findings(self, partial_output: dict, output_path: str) -> dict: ...


class ScoringHandler:
    """Facade coordinating principle resolution, unit scoring, and batch severity evaluation."""

    def __init__(
        self,
        scorer_provider: PrincipleScorerProviding,
        files_scorer: FilesScoringCapable,
    ) -> None:
        self._scorer_provider = scorer_provider
        self._files_scorer = files_scorer

    def resolve_and_score(self, files: list) -> tuple[list, Optional[dict]]:
        if not files:
            return [], None
        scored_files, err = self._files_scorer.score_files(self._scorer_provider, files)
        return scored_files, err

    def score_severity(self, partial_outputs: list) -> dict[str, Any]:
        results = []
        for idx, entry in enumerate(partial_outputs):
            scored_files, error = self.resolve_and_score(entry.get("files", []))
            if error:
                results.append({**error, "entry_index": idx})
                continue
            scored_entry = dict(entry)
            scored_entry["files"] = scored_files
            results.append(scored_entry)
        return {"results": results}
