"""Persists one aggregate review result in the normalized result directory."""

from pathlib import Path

from harness.review_result import ReviewResult
from harness.review_result_persisting import ReviewResultPersisting


_RESULT_PATH = Path("results") / "review" / "result.json"


"""
solid-name: ReviewResultPersister
solid-category: service
solid-spec: [SPEC-039]
solid-description: Persists the authoritative aggregate review result at its stable run-relative location.
"""
class ReviewResultPersister(ReviewResultPersisting):
    def persist(
        self,
        run_directory: Path,
        result: ReviewResult,
    ) -> None:
        result_path = run_directory / _RESULT_PATH
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8",
        )
