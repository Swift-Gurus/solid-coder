"""Scores immutable principle submissions without mapping-based business interfaces."""

from dataclasses import replace

from findings.principle_scoring_result import PrincipleScoringResult
from findings.principle_submission import PrincipleSubmission
from findings.principle_submission_scoring import PrincipleSubmissionScoring
from scoring.review_unit_scoring import ReviewUnitScoring


"""
solid-name: PrincipleSubmissionScorer
solid-category: service
solid-description: Applies server-authoritative unit scoring across every file in an immutable principle submission.
"""
class PrincipleSubmissionScorer(PrincipleSubmissionScoring):
    def __init__(self, unit_scoring: ReviewUnitScoring) -> None:
        self._unit_scoring = unit_scoring

    def score(self, submission: PrincipleSubmission) -> PrincipleScoringResult:
        scored_files = []
        for reviewed_file in submission.output.files:
            scored_units = []
            for unit in reviewed_file.units:
                result = self._unit_scoring.score(unit, reviewed_file.file_path)
                if not result.succeeded or result.unit is None:
                    return PrincipleScoringResult(
                        error_message=result.error_message
                    )
                scored_units.append(result.unit)
            scored_files.append(
                replace(reviewed_file, units=tuple(scored_units))
            )

        return PrincipleScoringResult(
            output=replace(
                submission.output,
                files=tuple(scored_files),
            )
        )
