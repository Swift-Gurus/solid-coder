from pydantic import BaseModel, ConfigDict, Field
from source.analysis.relationships.source_declaration_reference import (
    SourceDeclarationReference,
)
from source.analysis.relationships.source_relationship_status import (
    SourceRelationshipStatus,
)
from source.source_unit_identity import SourceUnitIdentity

"""
solid-name: SourceDeclarationRelationship
solid-category: model
solid-spec: [SPEC-057]
solid-description: Retains candidate declaration identities and the uncertainty explaining a bounded source relationship.
"""


class SourceDeclarationRelationship(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reference: SourceDeclarationReference
    status: SourceRelationshipStatus
    candidates: list[SourceUnitIdentity] = Field(default_factory=list)
    reason: str = Field(min_length=1)
