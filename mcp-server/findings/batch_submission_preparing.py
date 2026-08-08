"""Defines context-aware preparation of findings batches."""

from typing import Protocol

from findings.batch_submission import BatchSubmission
from findings.prepared_batch_submission import PreparedBatchSubmission


"""
solid-name: BatchSubmissionPreparing
solid-category: abstraction
solid-description: Contract for applying requested health context and validating unit coverage before batch persistence.
"""
class BatchSubmissionPreparing(Protocol):
    def prepare(
        self,
        output_dir: str,
        submission: BatchSubmission,
    ) -> PreparedBatchSubmission: ...
