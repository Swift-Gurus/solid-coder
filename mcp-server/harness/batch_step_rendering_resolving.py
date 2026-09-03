"""Defines resolution of rendering for a batch-presentation mode."""

from typing import Protocol

from harness.batch_step_presentation_mode import BatchStepPresentationMode
from harness.batch_step_rendering import BatchStepRendering


"""
solid-name: BatchStepRenderingResolving
solid-category: abstraction
solid-spec: [SPEC-042, SPEC-043]
solid-description: Contract for resolving model-facing batch rendering by presentation mode.
"""
class BatchStepRenderingResolving(Protocol):
    def resolve(
        self,
        mode: BatchStepPresentationMode,
    ) -> BatchStepRendering: ...
