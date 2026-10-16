from pydantic import BaseModel, ConfigDict

from source.analysis.relationships.source_relationship_inventory import SourceRelationshipInventory
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: SourceDeclarationMembersInput
solid-category: model
solid-spec: [SPEC-057]
solid-description: Identifies a declaration within an inspected relationship inventory for deterministic declared and extension member analysis.
"""
class SourceDeclarationMembersInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    inventory: SourceRelationshipInventory
    declaration: SourceUnitIdentity
