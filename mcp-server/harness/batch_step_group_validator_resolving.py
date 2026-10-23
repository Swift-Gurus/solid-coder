"""Defines resolution of validation for a batch-presentation mode."""

from typing import Protocol

from harness.batch_step_group_validating import BatchStepGroupValidating
from harness.batch_step_presentation_mode import BatchStepPresentationMode

"""
solid-name: BatchStepGroupValidatorResolving
solid-category: abstraction
solid-spec: [SPEC-042, SPEC-043]
solid-description: Contract for selecting validation behavior for each batch presentation mode.
"""


class BatchStepGroupValidatorResolving(Protocol):
    def resolve(
        self,
        mode: BatchStepPresentationMode,
    ) -> BatchStepGroupValidating: ...
