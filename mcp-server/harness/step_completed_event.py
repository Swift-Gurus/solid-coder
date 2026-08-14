"""Defines the typed payload of a persisted step-completion event."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: StepCompletedEvent
solid-category: model
solid-spec: [SPEC-010, SPEC-030]
solid-description: Represents persisted step completion state for one workflow instance and its parent step.
"""
class StepCompletedEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    step_id: str = ""
    instance_id: str = ""
    outputs: dict[str, Any] = Field(default_factory=dict)
    iteration_index: Optional[int] = None
    item: Any = None
    parent_completed: bool = True
    empty_collection: bool = False
