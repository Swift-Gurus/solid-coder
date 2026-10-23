from pydantic import BaseModel, ConfigDict, Field
from source.analysis.calls.source_call import SourceCall
from source.members.source_member import SourceMember

"""
solid-name: SourceContractMembers
solid-category: model
solid-spec: [SPEC-067]
solid-description: Carries matched contract implementations, actual invocation evidence and unresolved coverage for one reviewed source declaration.
"""


class SourceContractMembers(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    members: list[SourceMember] = Field(default_factory=list)
    calls: list[SourceCall] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    context: str = ""
