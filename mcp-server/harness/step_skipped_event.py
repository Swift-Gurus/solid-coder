"""Defines the persisted payload for a skipped workflow-step instance."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from harness.condition_evidence import ConditionEvidence
from harness.unavailable_condition_evidence import UnavailableConditionEvidence


"""
solid-name: StepSkippedEvent
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents persisted state for one conditionally skipped workflow-step instance.
"""
class StepSkippedEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    step_id: str
    instance_id: str
    condition: object
    evidence: ConditionEvidence = Field(
        default_factory=lambda: UnavailableConditionEvidence(matched=False)
    )
    item: Any = None
    iteration_index: Optional[int] = None
    workflow_instance_id: Optional[str] = None
    local_step_id: Optional[str] = None
    workflow_source_index: Optional[int] = None
    parent_completed: bool = True
