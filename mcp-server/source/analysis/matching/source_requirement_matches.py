from pydantic import BaseModel, ConfigDict, Field
from source.analysis.matching.source_requirement_match import SourceRequirementMatch
from source.analysis.relationships.source_declaration_relationship import (
    SourceDeclarationRelationship,
)
from source.analysis.relationships.source_relationship_inventory import (
    SourceRelationshipInventory,
)

"""
solid-name: SourceRequirementMatches
solid-category: model
solid-spec: [SPEC-057]
solid-description: Retains ordered requirement matches alongside the inspected source snapshots and bounded relationship evidence used to derive them.
"""


class SourceRequirementMatches(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    inventory: SourceRelationshipInventory
    relationship: SourceDeclarationRelationship
    matches: list[SourceRequirementMatch] = Field(default_factory=list)
