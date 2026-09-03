"""Defines the structured workflow-group presentation declaration."""

from pydantic import BaseModel, ConfigDict

from harness.workflow_presentation_mode import WorkflowPresentationMode


"""
solid-name: WorkflowPresentationDeclaration
solid-category: model
solid-spec: [SPEC-043]
solid-description: Validates one authored workflow-group presentation mode at the structured-input boundary.
"""
class WorkflowPresentationDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: WorkflowPresentationMode = WorkflowPresentationMode.INDIVIDUAL
