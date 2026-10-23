"""Authoritative metadata checks for one source declaration."""

from pydantic import BaseModel, ConfigDict
from source.analysis.declarations.source_scoped_declaration import (
    SourceScopedDeclaration,
)
from source.source_frontmatter import SourceFrontmatter
from source.technology_detection import TechnologyDetection

"""
solid-name: SourceFrontmatterInspection
solid-category: model
solid-spec: [SPEC-069]
solid-description: Records declaration-owned metadata, structural exclusions and mechanically verified field validity.
"""


class SourceFrontmatterInspection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    declaration: SourceScopedDeclaration
    metadata: SourceFrontmatter
    has_frontmatter: bool
    missing_exempt: bool
    name_matches: bool
    category_registered: bool
    stack_matches: bool
    bad_description: bool
    stack_evidence: list[TechnologyDetection]
