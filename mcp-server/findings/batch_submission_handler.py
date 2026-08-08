"""Provides the public batch findings submission facade."""

from findings.batch_submission_handling import BatchSubmissionHandling
from findings.batch_submission_parse_result import BatchSubmissionParseResult


class BatchSubmissionHandler(BatchSubmissionHandling):
    """
    solid-name: BatchSubmissionHandler
    solid-category: service
    solid-description: Delegates typed batch findings requests to the configured submission workflow.
    """

    def __init__(self, coordinator: BatchSubmissionHandling) -> None:
        self._coordinator = coordinator

    def submit_batch(
        self,
        output_dir: str,
        parse_result: BatchSubmissionParseResult,
    ) -> dict:
        return self._coordinator.submit_batch(output_dir, parse_result)
