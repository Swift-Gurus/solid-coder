"""Constructs rejected original-instance output mappings."""

from harness.rejected_step_output_mapping_building import (
    RejectedStepOutputMappingBuilding,
)
from harness.step_output_submission_mapping_result import StepOutputSubmissionMappingResult


"""
solid-name: RejectedStepOutputMappingBuilder
solid-category: service
solid-spec: [SPEC-045]
solid-description: Constructs a rejected mapping result with an actionable model-output error.
"""
class RejectedStepOutputMappingBuilder(RejectedStepOutputMappingBuilding):
    def build(self, message: str) -> StepOutputSubmissionMappingResult:
        return StepOutputSubmissionMappingResult(outputs={}, error=message)
