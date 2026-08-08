"""Scores and persists immutable principle submissions."""

from pathlib import Path

from findings.partial_review_output_persisting import PartialReviewOutputPersisting
from findings.principle_submission import PrincipleSubmission
from findings.principle_submission_result import PrincipleSubmissionResult
from findings.principle_submission_scoring import PrincipleSubmissionScoring
from findings.principle_submission_submitting import PrincipleSubmissionSubmitting


"""
solid-name: PrincipleSubmissionSubmitter
solid-category: service
solid-description: Coordinates typed server-authoritative scoring and persistence for one immutable principle submission.
"""
class PrincipleSubmissionSubmitter(PrincipleSubmissionSubmitting):
    def __init__(
        self,
        scoring: PrincipleSubmissionScoring,
        persisting: PartialReviewOutputPersisting,
    ) -> None:
        self._scoring = scoring
        self._persisting = persisting

    def submit(
        self,
        submission: PrincipleSubmission,
        output_path: Path,
    ) -> PrincipleSubmissionResult:
        scoring_result = self._scoring.score(submission)
        if not scoring_result.succeeded or scoring_result.output is None:
            return PrincipleSubmissionResult(scoring_result.error_message)

        self._persisting.persist(scoring_result.output, output_path)
        return PrincipleSubmissionResult()
