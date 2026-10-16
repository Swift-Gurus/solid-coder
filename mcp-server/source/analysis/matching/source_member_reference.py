from pydantic import BaseModel, ConfigDict, Field

from source.analysis.relationships.source_declaration_relationship import SourceDeclarationRelationship
from source.members.source_member import SourceMember
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: SourceMemberReference
solid-category: model
solid-spec: [SPEC-057]
solid-description: Preserves a candidate member's declaring owner, signature, source evidence, and bounded extension links.
"""
class SourceMemberReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    owner: SourceUnitIdentity
    member: SourceMember
    relationships: list[SourceDeclarationRelationship] = Field(default_factory=list)
