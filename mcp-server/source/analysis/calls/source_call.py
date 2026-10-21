from pydantic import BaseModel, ConfigDict, Field

from source.source_line_range import SourceLineRange


"""
solid-name: SourceCall
solid-category: model
solid-spec: [SPEC-067]
solid-description: Records an authored invocation with exact source coordinates, callee syntax and argument labels without claiming resolved dispatch or reachability.
"""
class SourceCall(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity: str = Field(min_length=1)
    callee: str = Field(min_length=1)
    argument_labels: list[str] = Field(default_factory=list)
    expression: str = Field(min_length=1)
    span: SourceLineRange
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
