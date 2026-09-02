"""Defines typed sibling identity for one model-facing batch."""

from dataclasses import dataclass
from typing import Optional


"""
solid-name: BatchStepGroupIdentity
solid-category: model
solid-spec: [SPEC-042]
solid-description: Identifies sibling ready work by optional included-workflow ownership and authored local step identity without encoding structure into a string.
"""
@dataclass(frozen=True)
class BatchStepGroupIdentity:
    workflow_alias: Optional[str]
    local_step_id: str
