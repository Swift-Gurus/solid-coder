"""Defines ordered persistence of immutable findings batches."""

from typing import Protocol

from findings.batch_persistence_result import BatchPersistenceResult
from findings.batch_submission import BatchSubmission


"""
solid-name: BatchSubmissionPersisting
solid-category: abstraction
solid-description: Contract for persisting principle reviews in batch order and reporting the first failure.
"""
class BatchSubmissionPersisting(Protocol):
    def persist(
        self,
        output_dir: str,
        submission: BatchSubmission,
    ) -> BatchPersistenceResult: ...
