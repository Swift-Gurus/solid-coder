"""Defines resolution of submission mapping by batch-presentation mode."""

from typing import Protocol

from harness.batch_step_presentation_mode import BatchStepPresentationMode
from harness.step_output_submission_mapping import StepOutputSubmissionMapping


"""
solid-name: BatchOutputSubmissionMappingResolving
solid-category: abstraction
solid-spec: [SPEC-042, SPEC-043]
solid-description: Contract for resolving output-submission mapping by batch-presentation mode.
"""
class BatchOutputSubmissionMappingResolving(Protocol):
    def resolve(
        self,
        mode: BatchStepPresentationMode,
    ) -> StepOutputSubmissionMapping: ...
