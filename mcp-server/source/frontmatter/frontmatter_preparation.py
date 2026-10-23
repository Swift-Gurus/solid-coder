"""Auditable deterministic preparation for metadata review."""

from pydantic import BaseModel, ConfigDict, Field
from source.frontmatter.source_description_target import SourceDescriptionTarget
from source.frontmatter.source_frontmatter_inspection import SourceFrontmatterInspection
from source.frontmatter.stack_registration import StackRegistration

"""
solid-name: FrontmatterPreparation
solid-category: model
solid-spec: [SPEC-069]
solid-description: Preserves ordered metadata facts, description targets, effective vocabulary and explicit inspection limitations.
"""


class FrontmatterPreparation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    entries: list[SourceFrontmatterInspection] = Field(default_factory=list)
    descriptions: list[SourceDescriptionTarget] = Field(default_factory=list)
    categories: list[str]
    stack_registrations: list[StackRegistration]
    limitations: list[str] = Field(default_factory=list)
