"""Declares successful step-output mapping construction."""

from typing import Protocol

from harness.step_output_submission_mapping_result import StepOutputSubmissionMappingResult


"""
solid-name: SuccessfulStepOutputMappingBuilding
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for constructing a successful original-instance output mapping.
"""
class SuccessfulStepOutputMappingBuilding(Protocol):
    def build(self, outputs: dict) -> StepOutputSubmissionMappingResult: ...
