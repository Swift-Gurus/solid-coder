"""Loads authoritative aggregate review results from flow-run storage."""

from pathlib import Path

from harness.review_result import ReviewResult
from harness.isolated_run_paths import ISOLATED_RUNS_DIRNAME
from harness.runs_base_dir_resolving import RunsBaseDirResolving


_RESULT_PATH = Path("results") / "review" / "result.json"


"""
solid-name: FlowReviewResultReader
solid-category: service
solid-spec: [SPEC-036, SPEC-039]
solid-description: Loads and validates the aggregate review result for one identified flow run.
"""
class FlowReviewResultReader:
    def __init__(self, base_directory: RunsBaseDirResolving) -> None:
        self._base_directory = base_directory

    def read(self, run_id: str) -> ReviewResult:
        if not run_id or Path(run_id).name != run_id:
            raise ValueError("Run ID must be a non-empty path component")
        result_path = (
            self._base_directory.resolve()
            / ISOLATED_RUNS_DIRNAME
            / run_id
            / _RESULT_PATH
        )
        return ReviewResult.model_validate_json(
            result_path.read_text(encoding="utf-8")
        )
