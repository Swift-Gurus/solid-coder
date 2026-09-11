"""Constructs successful original-instance output mappings."""

from harness.step_output_submission_mapping_result import StepOutputSubmissionMappingResult
from harness.successful_step_output_mapping_building import (
    SuccessfulStepOutputMappingBuilding,
)


"""
solid-name: SuccessfulStepOutputMappingBuilder
solid-category: service
solid-spec: [SPEC-045]
solid-description: Constructs a successful mapping from model outputs to original step instances.
"""
class SuccessfulStepOutputMappingBuilder(SuccessfulStepOutputMappingBuilding):
    def build(self, outputs: dict) -> StepOutputSubmissionMappingResult:
        return StepOutputSubmissionMappingResult(outputs=outputs)
