"""Defines an exact half-open source byte range."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


"""
solid-name: SourceByteRange
solid-category: model
solid-spec: [SPEC-063, SPEC-064]
solid-description: Records an exact half-open UTF-8 source range.
"""
class SourceByteRange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    start: int = Field(ge=0)
    end: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_order(self) -> "SourceByteRange":
        if self.end < self.start:
            raise ValueError("A source byte range cannot end before it starts.")
        return self
