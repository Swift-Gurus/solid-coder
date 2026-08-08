"""Rejects typed health-check batches submitted before a valid DRY search."""

from findings.batch_submission_handling import BatchSubmissionHandling
from findings.batch_submission_parse_result import BatchSubmissionParseResult
from health.dry_search_completion_checking import DrySearchCompletionChecking
from health.dry_search_completion_status import DrySearchCompletionStatus


"""
solid-name: DrySearchEnforcingBatchFindingsSubmitter
solid-category: service
solid-description: Enforces successful DRY-search completion before accepting a typed health-check findings batch.
"""
class DrySearchEnforcingBatchFindingsSubmitter(BatchSubmissionHandling):
    def __init__(
        self,
        submission: BatchSubmissionHandling,
        completion: DrySearchCompletionChecking,
    ) -> None:
        self._submission = submission
        self._completion = completion

    def submit_batch(
        self,
        output_dir: str,
        parse_result: BatchSubmissionParseResult,
    ) -> dict:
        status = self._completion.status(output_dir)
        if status is DrySearchCompletionStatus.MISSING:
            return {
                "error": "dry_search_required",
                "message": (
                    "Run mcp__pipeline__search_codebase with query and this same "
                    "output_dir before submitting health-check findings."
                ),
            }
        return self._submission.submit_batch(output_dir, parse_result)
