"""Defines one model-facing item in a batched workflow step."""

from dataclasses import dataclass

from harness.batch_step_group_identity import BatchStepGroupIdentity

"""
solid-name: BatchStepPresentation
solid-category: model
solid-spec: [SPEC-042]
solid-description: Associates one internal ready instance with its batch group and compact domain label without exposing engine identity to the model.
"""
@dataclass(frozen=True)
class BatchStepPresentation:
    group: BatchStepGroupIdentity
    label: str
