"""Defines the structured workflow execution declaration."""

from pydantic import BaseModel, ConfigDict

from harness.workflow_execution_mode import WorkflowExecutionMode


"""
solid-name: WorkflowExecutionDeclaration
solid-category: model
solid-spec: [SPEC-045]
solid-description: Validates one authored workflow execution mode at the structured-input boundary.
"""
class WorkflowExecutionDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: WorkflowExecutionMode = WorkflowExecutionMode.GRANULAR
