"""Defines an inline workflow group entry."""

from __future__ import annotations

from typing import Union

from pydantic import BaseModel, ConfigDict

from harness.step_declaration import StepDeclaration
from harness.uses_workflow_entry import UsesWorkflowEntry
from harness.workflow_include_entry import WorkflowIncludeEntry


"""
solid-name: InlineWorkflowGroup
solid-category: model
solid-spec: [SPEC-027]
solid-description: Represents a named inline group containing typed workflow entries.
"""
class InlineWorkflowGroup(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    group: str
    steps: list[
        Union[
            StepDeclaration,
            WorkflowIncludeEntry,
            UsesWorkflowEntry,
            InlineWorkflowGroup,
        ]
    ]
