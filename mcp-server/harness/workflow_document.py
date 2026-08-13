"""Defines a parsed workflow document."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from harness.workflow_entry import WorkflowEntry


"""
solid-name: WorkflowDocument
solid-category: model
solid-spec: [SPEC-030, SPEC-035]
solid-description: Represents a workflow document immediately after structured-input validation.
"""
class WorkflowDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: Optional[str] = None
    name: str = ""
    max_turns: int = 10
    steps: list[WorkflowEntry] = Field(default_factory=list)
