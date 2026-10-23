from pydantic import BaseModel, ConfigDict
from source.analysis.matching.source_member_contribution import SourceMemberContribution
from source.analysis.relationships.source_relationship_inventory import (
    SourceRelationshipInventory,
)
from source.source_unit_identity import SourceUnitIdentity

"""
solid-name: SourceDeclarationMembers
solid-category: model
solid-spec: [SPEC-057]
solid-description: Carries ordered declared and extension member contributions together with the inspected source inventory and its bounded relationship evidence.
"""


class SourceDeclarationMembers(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    inventory: SourceRelationshipInventory
    declaration: SourceUnitIdentity
    members: list[SourceMemberContribution]
