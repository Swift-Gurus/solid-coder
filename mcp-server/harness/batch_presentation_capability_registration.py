"""Registers one batch-presentation mode with a typed capability."""

from dataclasses import dataclass
from typing import Generic, TypeVar

from harness.batch_step_presentation_mode import BatchStepPresentationMode


Capability = TypeVar("Capability")


"""
solid-name: BatchPresentationCapabilityRegistration
solid-category: model
solid-spec: [SPEC-042, SPEC-043]
solid-description: Associates one batch-presentation mode with a typed runtime capability.
"""
@dataclass(frozen=True)
class BatchPresentationCapabilityRegistration(Generic[Capability]):
    mode: BatchStepPresentationMode
    capability: Capability
