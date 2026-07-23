"""
solid-name: StepHandling
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for handlers that execute steps and validate submissions.
"""

from __future__ import annotations

from typing import Protocol

from harness.step_running import StepRunning
from harness.step_submission_validating import StepSubmissionValidating


class StepHandling(StepRunning, StepSubmissionValidating, Protocol):
    """
    solid-name: StepHandling
    solid-category: abstraction
    solid-spec: [SPEC-027]
    solid-description: Contract for handlers that execute steps and validate submissions.
    """
