"""Defines the result of preparing one findings batch."""

from dataclasses import dataclass
from typing import Optional

from findings.batch_coverage_failure import BatchCoverageFailure
from findings.batch_submission import BatchSubmission


"""
solid-name: PreparedBatchSubmission
solid-category: model
solid-description: Carries a context-adjusted findings batch and any detected unit-coverage failure.
"""
@dataclass(frozen=True)
class PreparedBatchSubmission:
    submission: BatchSubmission
    coverage_failure: Optional[BatchCoverageFailure] = None
