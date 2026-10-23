"""Defines the validated authored workflow-output collection."""

from __future__ import annotations

from harness.authored_workflow_output import AuthoredWorkflowOutput
from pydantic import RootModel, model_validator

"""
solid-name: AuthoredWorkflowOutputs
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents a validated collection of authored workflow outputs.
"""


class AuthoredWorkflowOutputs(RootModel[list[AuthoredWorkflowOutput]]):
    @model_validator(mode="after")
    def require_unique_names(self) -> AuthoredWorkflowOutputs:
        names = [output.name for output in self.root]
        if len(names) != len(set(names)):
            raise ValueError("workflow output names must be unique")
        return self
