"""Prepares immutable findings batches for persistence."""

from findings.batch_coverage_validating import BatchCoverageValidating
from findings.batch_submission import BatchSubmission
from findings.batch_submission_preparing import BatchSubmissionPreparing
from findings.prepared_batch_submission import PreparedBatchSubmission
from findings.requested_hook_context_loading import RequestedHookContextLoading
from findings.submission_context_applying import SubmissionContextApplying


"""
solid-name: BatchSubmissionPreparer
solid-category: service
solid-description: Applies requested health context and verifies unit coverage for one immutable findings batch.
"""
class BatchSubmissionPreparer(BatchSubmissionPreparing):
    def __init__(
        self,
        context_loader: RequestedHookContextLoading,
        context_applier: SubmissionContextApplying,
        coverage_validator: BatchCoverageValidating,
    ) -> None:
        self._context_loader = context_loader
        self._context_applier = context_applier
        self._coverage_validator = coverage_validator

    def prepare(
        self,
        output_dir: str,
        submission: BatchSubmission,
    ) -> PreparedBatchSubmission:
        context = self._context_loader.load(output_dir)
        prepared_submission = self._context_applier.apply(submission, context)
        return PreparedBatchSubmission(
            submission=prepared_submission,
            coverage_failure=self._coverage_validator.validate(
                prepared_submission,
                context,
            ),
        )
