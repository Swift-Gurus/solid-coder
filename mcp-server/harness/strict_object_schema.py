"""Defines a strict JSON object-schema representation."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: StrictObjectSchema
solid-category: model
solid-spec: [SPEC-045]
solid-description: Represents a JSON object schema whose declared properties are closed and required explicitly.
"""
class StrictObjectSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str = "object"
    properties: dict[str, object] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    additional_properties: bool = Field(
        default=False,
        serialization_alias="additionalProperties",
    )
