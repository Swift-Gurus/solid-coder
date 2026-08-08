"""Defines MCP response construction for batch findings submission."""

from typing import Protocol

from findings.batch_coverage_failure import BatchCoverageFailure
from findings.batch_persistence_result import BatchPersistenceResult
from findings.batch_submission_parse_failure import BatchSubmissionParseFailure


"""
solid-name: BatchSubmissionResponseFormatting
solid-category: abstraction
solid-description: Contract for rendering typed batch completion and rejection outcomes as model-facing responses.
"""
class BatchSubmissionResponseFormatting(Protocol):
    def format_coverage_failure(self, failure: BatchCoverageFailure) -> dict: ...

    def format_parse_failure(self, failure: BatchSubmissionParseFailure) -> dict: ...

    def format_persistence_failure(self, failure: BatchPersistenceResult) -> dict: ...

    def format_success(self, output_dir: str) -> dict: ...
