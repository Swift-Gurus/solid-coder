"""Declares rejected step-output mapping construction."""

from typing import Protocol

from harness.step_output_submission_mapping_result import StepOutputSubmissionMappingResult


"""
solid-name: RejectedStepOutputMappingBuilding
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for constructing a rejected original-instance output mapping.
"""
class RejectedStepOutputMappingBuilding(Protocol):
    def build(self, message: str) -> StepOutputSubmissionMappingResult: ...
