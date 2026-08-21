"""Defines typed solid metadata decoded from source frontmatter YAML."""

from typing import Annotated

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
)


def _string_list(value: object) -> object:
    if isinstance(value, str):
        return [value]
    return value


FrontmatterStringList = Annotated[list[str], BeforeValidator(_string_list)]


"""
solid-name: SourceFrontmatter
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries typed name, responsibility, classification, tags, stack, and specification metadata from one source frontmatter block.
"""
class SourceFrontmatter(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(default="", validation_alias="solid-name")
    description: str = Field(
        default="",
        validation_alias="solid-description",
    )
    category: str = Field(default="", validation_alias="solid-category")
    tags: FrontmatterStringList = Field(
        default_factory=list,
        validation_alias="solid-tags",
    )
    stack: FrontmatterStringList = Field(
        default_factory=list,
        validation_alias="solid-stack",
    )
    specs: FrontmatterStringList = Field(
        default_factory=list,
        validation_alias="solid-spec",
    )
