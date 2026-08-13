"""Defines a workflow include entry."""

from typing import Union

from pydantic import BaseModel, ConfigDict, Field

from harness.workflow_include_reference import WorkflowIncludeReference


"""
solid-name: WorkflowIncludeEntry
solid-category: model
solid-spec: [SPEC-027, SPEC-035]
solid-description: Represents a path-based or catalog-ID workflow include and its local alias.
"""
class WorkflowIncludeEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    include: Union[str, WorkflowIncludeReference]
    alias: str = Field(validation_alias="as")
