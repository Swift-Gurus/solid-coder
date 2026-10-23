from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from source.analysis.relationships.source_declaration_relationship import (
    SourceDeclarationRelationship,
)
from source.source_analysis import SourceAnalysis

"""
solid-name: SourceRelationshipInventory
solid-category: model
solid-spec: [SPEC-057]
solid-description: Preserves inspected source facts, diagnostics, and bounded relationship candidates without claiming repository completeness or verified conformance.
"""


class SourceRelationshipInventory(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scope: Literal["supplied_top_level_sources"] = "supplied_top_level_sources"
    verification: Literal["unverified_candidates"] = "unverified_candidates"
    analyses: list[SourceAnalysis]
    relationships: list[SourceDeclarationRelationship] = Field(default_factory=list)
