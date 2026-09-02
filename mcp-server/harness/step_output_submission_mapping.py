"""Defines translation of model-facing output keys to ready step instances."""

from typing import Protocol

from harness.models import StepInstance
from harness.step_output_submission_mapping_result import (
    StepOutputSubmissionMappingResult,
)


"""
solid-name: StepOutputSubmissionMapping
solid-category: abstraction
solid-spec: [SPEC-042]
solid-description: Contract for adapting model-facing step output keys before ordinary per-instance validation.
"""
class StepOutputSubmissionMapping(Protocol):
    def map(
        self,
        ready: list[StepInstance],
        outputs: dict,
    ) -> StepOutputSubmissionMappingResult: ...
