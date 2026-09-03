"""Defines one non-scored output retained by an aggregate rule assessment."""

from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


"""
solid-name: RuleAssessmentSupportingOutput
solid-category: model
solid-spec: [SPEC-044]
solid-description: Declares one supporting analysis output that accompanies aggregate observations without participating in scoring.
"""
class RuleAssessmentSupportingOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    type: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    schema_value: Optional[dict[str, object]] = Field(
        default=None,
        validation_alias="schema",
        serialization_alias="schema",
    )
    schema_file: Optional[
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    ] = None
