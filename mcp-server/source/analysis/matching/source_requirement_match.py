from pydantic import BaseModel, ConfigDict, Field

from source.analysis.matching.source_member_reference import SourceMemberReference
from source.analysis.relationships.source_relationship_status import SourceRelationshipStatus
from source.members.source_member import SourceMember
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: SourceRequirementMatch
solid-category: model
solid-spec: [SPEC-057]
solid-description: Records bounded implementation candidates for one interface requirement with explicit ambiguity or insufficient-evidence reasoning.
"""
class SourceRequirementMatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    interface: SourceUnitIdentity
    requirement: SourceMember
    status: SourceRelationshipStatus
    candidates: list[SourceMemberReference] = Field(default_factory=list)
    reason: str = Field(min_length=1)
