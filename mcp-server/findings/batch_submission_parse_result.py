"""Defines the result of parsing an ordered findings batch."""

from dataclasses import dataclass
from typing import Optional

from findings.batch_submission import BatchSubmission
from findings.batch_submission_parse_failure import BatchSubmissionParseFailure


"""
solid-name: BatchSubmissionParseResult
solid-category: model
solid-description: Carries the valid submission prefix and the first optional labelled parsing failure.
"""
@dataclass(frozen=True)
class BatchSubmissionParseResult:
    submission: BatchSubmission
    failure: Optional[BatchSubmissionParseFailure] = None
