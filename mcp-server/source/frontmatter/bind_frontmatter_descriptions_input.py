"""Input boundary for complete description judgment accounting."""

from pydantic import BaseModel, ConfigDict, Field
from source.frontmatter.source_description_classification import (
    SourceDescriptionClassification,
)
from source.frontmatter.source_description_target import SourceDescriptionTarget
from source.frontmatter.source_frontmatter_inspection import SourceFrontmatterInspection

"""
solid-name: BindFrontmatterDescriptionsInput
solid-category: model
solid-spec: [SPEC-069]
solid-description: Associates authored description judgments with the authoritative metadata preparation requiring them.
"""


class BindFrontmatterDescriptionsInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    entries: list[SourceFrontmatterInspection]
    targets: list[SourceDescriptionTarget]
    classifications: list[SourceDescriptionClassification] = Field(default_factory=list)
