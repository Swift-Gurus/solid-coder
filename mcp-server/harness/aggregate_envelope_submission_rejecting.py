"""Declares malformed aggregate-envelope rejection."""

from typing import Protocol

from harness.batch_submission_target import BatchSubmissionTarget
from harness.step_output_submission_mapping_result import (
    StepOutputSubmissionMappingResult,
)


"""
solid-name: AggregateEnvelopeSubmissionRejecting
solid-category: abstraction
solid-spec: [SPEC-052]
solid-description: Contract for rejecting a malformed aggregate envelope with recovery guidance.
"""
class AggregateEnvelopeSubmissionRejecting(Protocol):
    def reject(
        self,
        reason: str,
        targets: list[BatchSubmissionTarget],
    ) -> StepOutputSubmissionMappingResult: ...
