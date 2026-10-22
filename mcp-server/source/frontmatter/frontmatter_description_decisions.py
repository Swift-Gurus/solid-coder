"""Validated collection of declaration description outcomes."""

from pydantic import BaseModel, ConfigDict

from source.frontmatter.source_description_classification import SourceDescriptionClassification


"""
solid-name: FrontmatterDescriptionDecisions
solid-category: model
solid-spec: [SPEC-069]
solid-description: Carries exactly-once description decisions for deterministic metadata scoring.
"""
class FrontmatterDescriptionDecisions(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    descriptions: list[SourceDescriptionClassification]
