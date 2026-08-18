"""Persists the deterministic result of one executable review rule."""

from pathlib import Path

from harness.review_result import ReviewResult
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
        review_directory = run_directory / _RESULTS_DIRECTORY
        rule_directory = (
            review_directory / result.workflow_id / result.rule_instance_id
        )
        rule_directory.mkdir(parents=True, exist_ok=True)
        (rule_directory / _RESULT_FILE_NAME).write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8",
        )

        (review_directory / _RESULT_FILE_NAME).write_text(
            ReviewResult(
                workflow_id=result.workflow_id,
                severity=result.severity,
                rule_results=[result],
            ).model_dump_json(indent=2),
            encoding="utf-8",
        )
