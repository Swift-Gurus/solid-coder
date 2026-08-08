"""Defines optional decoration of typed batch-submission handling."""

from typing import Protocol

from findings.batch_submission_handling import BatchSubmissionHandling


"""
solid-name: BatchSubmissionDecorating
solid-category: abstraction
solid-description: Contract for applying an optional submission policy around typed batch handling.
"""
class BatchSubmissionDecorating(Protocol):
    def make_submission(
        self,
        submission: BatchSubmissionHandling,
    ) -> BatchSubmissionHandling: ...
