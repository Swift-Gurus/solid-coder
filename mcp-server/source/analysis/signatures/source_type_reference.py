"""An authored type reference without inferred symbol resolution."""

from pydantic import BaseModel, ConfigDict, Field
from source.source_line_range import SourceLineRange

"""
solid-name: SourceTypeReference
solid-category: model
solid-spec: [SPEC-057]
solid-description: Preserves ordered type-name tokens and source evidence without claiming a resolved declaration identity.
"""


class SourceTypeReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tokens: list[str] = Field(min_length=1)
    span: SourceLineRange
