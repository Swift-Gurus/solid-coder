"""Resolves a registered capability for one batch-presentation mode."""

from typing import Generic, TypeVar

from harness.batch_presentation_capability_registration import (
    BatchPresentationCapabilityRegistration,
)
from harness.batch_step_presentation_mode import BatchStepPresentationMode
from harness.flow_validation_error import FlowValidationError


Capability = TypeVar("Capability")


"""
solid-name: BatchPresentationCapabilityResolver
solid-category: service
solid-spec: [SPEC-042, SPEC-043]
solid-description: Resolves a typed registered capability for a batch-presentation mode.
"""
class BatchPresentationCapabilityResolver(Generic[Capability]):
    def __init__(
        self,
        registrations: list[
            BatchPresentationCapabilityRegistration[Capability]
        ],
    ) -> None:
        self._registrations = registrations

    def resolve(self, mode: BatchStepPresentationMode) -> Capability:
        for registration in self._registrations:
            if registration.mode is mode:
                return registration.capability
        raise FlowValidationError(
            f"Unsupported batch-presentation mode '{mode.value}'"
        )
