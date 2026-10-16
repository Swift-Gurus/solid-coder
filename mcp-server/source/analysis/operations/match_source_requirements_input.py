from pydantic import BaseModel, ConfigDict

from source.analysis.relationships.source_declaration_relationship import SourceDeclarationRelationship
from source.analysis.relationships.source_relationship_inventory import SourceRelationshipInventory


"""
solid-name: MatchSourceRequirementsInput
solid-category: model
solid-spec: [SPEC-057]
solid-description: Identifies a recorded inheritance relationship and its inspected source snapshot for bounded requirement matching.
"""
class MatchSourceRequirementsInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    inventory: SourceRelationshipInventory
    relationship: SourceDeclarationRelationship
