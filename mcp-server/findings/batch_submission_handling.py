"""Defines batch findings submission coordination."""

from typing import Protocol

from findings.batch_submission_parse_result import BatchSubmissionParseResult


"""
solid-name: BatchSubmissionHandling
solid-category: abstraction
solid-description: Contract for coordinating validated batch findings submission.
"""
class BatchSubmissionHandling(Protocol):
    def submit_batch(
        self,
        output_dir: str,
        parse_result: BatchSubmissionParseResult,
    ) -> dict: ...
