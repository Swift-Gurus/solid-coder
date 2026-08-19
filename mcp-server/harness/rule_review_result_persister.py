"""Persists the deterministic result of one executable review rule."""

from pathlib import Path

from harness.rule_review_result import RuleReviewResult
from harness.rule_review_result_persisting import RuleReviewResultPersisting


_RESULTS_DIRECTORY = Path("results") / "review"
_RESULT_FILE_NAME = "result.json"


"""
solid-name: RuleReviewResultPersister
solid-category: service
solid-spec: [SPEC-039]
solid-description: Publishes identified rule and single-rule aggregate projections in the normalized review-result directory.
"""
class RuleReviewResultPersister(RuleReviewResultPersisting):
    def persist(
        self,
        run_directory: Path,
        result: RuleReviewResult,
    ) -> None:
        rule_directory = (
            run_directory
            / _RESULTS_DIRECTORY
            / result.workflow_id
            / result.rule_instance_id
        )
        rule_directory.mkdir(parents=True, exist_ok=True)
        (rule_directory / _RESULT_FILE_NAME).write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8",
        )
