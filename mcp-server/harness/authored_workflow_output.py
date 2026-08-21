"""Defines one structurally validated authored workflow output."""

from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


"""
solid-name: AuthoredWorkflowOutput
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents the YAML fields accepted for one reusable-workflow output before resource resolution.
"""
class AuthoredWorkflowOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: Annotated[str, StringConstraints(min_length=1)]
    type: Annotated[str, StringConstraints(min_length=1)]
    value: Annotated[str, StringConstraints(min_length=1)]
    schema_value: Optional[dict] = Field(
        default=None,
        validation_alias="schema",
        serialization_alias="schema",
    )
    schema_file: Optional[
        Annotated[str, StringConstraints(min_length=1)]
    ] = None

    @model_validator(mode="after")
    def require_one_schema_source(self) -> "AuthoredWorkflowOutput":
        if self.schema_value is not None and self.schema_file is not None:
            raise ValueError(
                "must declare at most one of 'schema' or 'schema_file'"
            )
        return self
