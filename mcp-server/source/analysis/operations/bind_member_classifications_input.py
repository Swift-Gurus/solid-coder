from pydantic import BaseModel, ConfigDict
from source.members.source_member import SourceMember
from source.members.source_member_classification import SourceMemberClassification

"""
solid-name: BindMemberClassificationsInput
solid-category: model
solid-spec: [SPEC-067]
solid-description: Pairs an authoritative member inventory with submitted judgments for exact coverage validation and source-ordered consumption.
"""


class BindMemberClassificationsInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    members: list[SourceMember]
    classifications: list[SourceMemberClassification]
