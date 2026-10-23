"""Defines the JSON-schema subset inspected by workflow data validation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

"""
solid-name: WorkflowDataSchema
solid-category: model
solid-spec: [SPEC-053, SPEC-057]
solid-description: Represents array items, nested object fields, and retained reference definitions addressable by workflow conditions.
"""


class WorkflowDataSchema(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    type: str | None = None
    properties: dict[str, WorkflowDataSchema] = Field(default_factory=dict)
    items: WorkflowDataSchema | None = None
    definitions: dict[str, WorkflowDataSchema] = Field(
        default_factory=dict, alias="$defs"
    )

    def property(self, name: str) -> WorkflowDataSchema | None:
        return self.properties.get(name)
