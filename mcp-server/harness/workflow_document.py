"""Defines a parsed workflow document."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from harness.workflow_entry import WorkflowEntry
from harness.workflow_execution_declaration import WorkflowExecutionDeclaration
from harness.workflow_presentation_declaration import WorkflowPresentationDeclaration


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
    execution: WorkflowExecutionDeclaration = WorkflowExecutionDeclaration()
    presentation: WorkflowPresentationDeclaration = WorkflowPresentationDeclaration()
    steps: list[WorkflowEntry] = Field(default_factory=list)
