"""Defines typed sibling identity for one model-facing batch."""

from dataclasses import dataclass

"""
solid-name: BatchStepGroupIdentity
solid-category: model
solid-spec: [SPEC-042]
solid-description: Represents the identity of a sibling work item within a model-facing batch.
"""


@dataclass(frozen=True)
class BatchStepGroupIdentity:
    workflow_alias: str | None
    local_step_id: str
    owner_instance_id: str | None = None
