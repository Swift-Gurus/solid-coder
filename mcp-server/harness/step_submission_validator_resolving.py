"""Defines selection of workflow-step submission validation."""

from __future__ import annotations

from typing import Protocol

from harness.step_submission_validating import StepSubmissionValidating


"""
solid-name: StepSubmissionValidatorResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for resolving submission validation by workflow step type.
"""
class StepSubmissionValidatorResolving(Protocol):
    def resolve(self, step_type: str) -> StepSubmissionValidating: ...
