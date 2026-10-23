from pydantic import BaseModel, ConfigDict, Field
from source.analysis.matching.source_member_reference import SourceMemberReference
from source.analysis.matching.source_member_role import SourceMemberRole
from source.members.source_member import SourceMember

"""
solid-name: SourceMemberContribution
solid-category: model
solid-spec: [SPEC-057]
solid-description: Preserves a member's structural contribution, matching declarations, ownership evidence, and unresolved analysis reasons without assigning review policy.
"""


class SourceMemberContribution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reference: SourceMemberReference
    role: SourceMemberRole
    matching_declarations: list[SourceMember] = Field(default_factory=list)
    reason: str = Field(min_length=1)
