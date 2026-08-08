"""Defines application of health-check context to findings submissions."""

from typing import Optional, Protocol

from findings.batch_submission import BatchSubmission
from findings.hook_context import HookContext


"""
solid-name: SubmissionContextApplying
solid-category: abstraction
solid-description: Contract for applying authoritative health-check context to findings submissions.
"""
class SubmissionContextApplying(Protocol):
    def apply(
        self,
        submissions: BatchSubmission,
        context: Optional[HookContext],
    ) -> BatchSubmission: ...
