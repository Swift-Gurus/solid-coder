"""Defines typed scoring of immutable principle submissions."""

from typing import Protocol

from findings.principle_scoring_result import PrincipleScoringResult
from findings.principle_submission import PrincipleSubmission


"""
solid-name: PrincipleSubmissionScoring
solid-category: abstraction
solid-description: Contract for applying server-authoritative severity rules to one immutable principle submission.
"""
class PrincipleSubmissionScoring(Protocol):
    def score(self, submission: PrincipleSubmission) -> PrincipleScoringResult: ...
