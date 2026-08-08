"""Applies authoritative health-check context to findings submissions."""

from typing import Optional

from findings.batch_submission import BatchSubmission
from findings.hook_context import HookContext
from findings.partial_review_output import PartialReviewOutput
from findings.principle_submission import PrincipleSubmission
from findings.reviewed_file import ReviewedFile
from findings.submission_context_applying import SubmissionContextApplying


"""
solid-name: SubmissionContextApplier
solid-category: service
solid-description: Rewrites submitted file paths using the authoritative health-check file path.
"""
class SubmissionContextApplier(SubmissionContextApplying):
    def apply(
        self,
        submissions: BatchSubmission,
        context: Optional[HookContext],
    ) -> BatchSubmission:
        if context is None or not context.file_path:
            return submissions
        return BatchSubmission(
            principles=tuple(
                PrincipleSubmission(
                    label=submission.label,
                    output=PartialReviewOutput(
                        timestamp=submission.output.timestamp,
                        files=tuple(
                            ReviewedFile(
                                file_path=context.file_path,
                                units=reviewed_file.units,
                            )
                            for reviewed_file in submission.output.files
                        ),
                    ),
                )
                for submission in submissions.principles
            )
        )
