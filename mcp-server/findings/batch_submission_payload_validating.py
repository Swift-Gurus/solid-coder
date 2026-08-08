"""Defines validation of an external batch-submission payload."""

from typing import Protocol


"""
solid-name: BatchSubmissionPayloadValidating
solid-category: abstraction
solid-description: Contract for validating the shape of an external review batch payload.
"""
class BatchSubmissionPayloadValidating(Protocol):
    def is_valid(self, raw_submissions: object) -> bool: ...
