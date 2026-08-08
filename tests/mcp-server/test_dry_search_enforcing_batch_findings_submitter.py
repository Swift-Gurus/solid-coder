"""Verifies batch findings require DRY-search proof only for health checks."""

from unittest.mock import MagicMock

from findings.batch_submission import BatchSubmission
from findings.batch_submission_parse_result import BatchSubmissionParseResult
from health.dry_search_completion_status import DrySearchCompletionStatus
from health.dry_search_enforcing_batch_findings_submitter import (
    DrySearchEnforcingBatchFindingsSubmitter,
)


"""
solid-name: TestDrySearchEnforcingBatchFindingsSubmitter
solid-category: unit-test
solid-description: Verifies health-check submission is rejected without DRY-search proof while other submissions remain supported.
"""
class TestDrySearchEnforcingBatchFindingsSubmitter:
    def setup_method(self) -> None:
        self.submission = MagicMock()
        self.completion = MagicMock()
        self.handler = DrySearchEnforcingBatchFindingsSubmitter(
            submission=self.submission,
            completion=self.completion,
        )
        self.parse_result = BatchSubmissionParseResult(BatchSubmission(()))

    def test_missing_health_completion_is_rejected(self) -> None:
        self.completion.status.return_value = DrySearchCompletionStatus.MISSING

        result = self.handler.submit_batch("/health/run", self.parse_result)

        assert result["error"] == "dry_search_required"
        self.submission.submit_batch.assert_not_called()

    def test_completed_health_search_delegates_submission(self) -> None:
        self.completion.status.return_value = DrySearchCompletionStatus.COMPLETE
        self.submission.submit_batch.return_value = {"violations": []}

        result = self.handler.submit_batch("/health/run", self.parse_result)

        assert result == {"violations": []}
        self.submission.submit_batch.assert_called_once_with(
            "/health/run",
            self.parse_result,
        )

    def test_non_health_submission_does_not_require_completion(self) -> None:
        self.completion.status.return_value = DrySearchCompletionStatus.NOT_REQUIRED
        self.submission.submit_batch.return_value = {"violations": []}

        result = self.handler.submit_batch("/review/run", self.parse_result)

        assert result == {"violations": []}
        self.submission.submit_batch.assert_called_once()
