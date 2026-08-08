"""Defines unit-coverage validation for immutable findings batches."""

from typing import Optional, Protocol

from findings.batch_coverage_failure import BatchCoverageFailure
from findings.batch_submission import BatchSubmission
from findings.hook_context import HookContext


"""
solid-name: BatchCoverageValidating
solid-category: abstraction
solid-description: Contract for detecting required source units omitted from an immutable batch review.
"""
class BatchCoverageValidating(Protocol):
    def validate(
        self,
        submission: BatchSubmission,
        context: Optional[HookContext],
    ) -> Optional[BatchCoverageFailure]: ...
