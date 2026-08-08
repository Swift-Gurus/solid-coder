"""Defines submission of one immutable principle review."""

from pathlib import Path
from typing import Protocol

from findings.principle_submission import PrincipleSubmission
from findings.principle_submission_result import PrincipleSubmissionResult


"""
solid-name: PrincipleSubmissionSubmitting
solid-category: abstraction
solid-description: Contract for validating, scoring, and persisting one immutable principle review submission.
"""
class PrincipleSubmissionSubmitting(Protocol):
    def submit(
        self,
        submission: PrincipleSubmission,
        output_path: Path,
    ) -> PrincipleSubmissionResult: ...
