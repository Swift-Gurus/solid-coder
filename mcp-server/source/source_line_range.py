"""Defines an inclusive source line range."""

from pydantic import BaseModel, ConfigDict, model_validator


"""
solid-name: SourceLineRange
solid-category: model
solid-spec: [SPEC-040]
solid-description: Represents a validated inclusive range in destination-file line coordinates.
"""
class SourceLineRange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    start: int
    end: int

    @model_validator(mode="after")
    def validate_bounds(self) -> "SourceLineRange":
        if self.start < 1:
            raise ValueError("source line range start must be positive")
        if self.end < self.start:
            raise ValueError("source line range end must not precede start")
        return self
