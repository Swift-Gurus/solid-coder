"""Defines the validated authored workflow-output collection."""

from __future__ import annotations

from pydantic import RootModel, model_validator

from harness.authored_workflow_output import AuthoredWorkflowOutput


"""
solid-name: AuthoredWorkflowOutputs
solid-category: model
solid-spec: [SPEC-037]
solid-description: Validates uniqueness across the workflow outputs declared in one YAML document.
"""
class AuthoredWorkflowOutputs(RootModel[list[AuthoredWorkflowOutput]]):

    @model_validator(mode="after")
    def require_unique_names(self) -> "AuthoredWorkflowOutputs":
        names = [output.name for output in self.root]
        if len(names) != len(set(names)):
            raise ValueError("workflow output names must be unique")
        return self
