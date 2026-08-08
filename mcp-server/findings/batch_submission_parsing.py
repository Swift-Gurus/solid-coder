"""Defines parsing of an external findings batch submission."""

from typing import Protocol

from findings.batch_submission_parse_result import BatchSubmissionParseResult


"""
solid-name: BatchSubmissionParsing
solid-category: abstraction
solid-description: Contract for parsing an external review request into an immutable batch submission.
"""
class BatchSubmissionParsing(Protocol):
    def parse(self, raw_submissions: object) -> BatchSubmissionParseResult: ...
