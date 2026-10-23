from pydantic import BaseModel, ConfigDict, Field

"""
solid-name: SourceMemberClassification
solid-category: model
solid-spec: [SPEC-067]
solid-description: Associates an evidenced workflow-defined judgment with one authoritative member identity without embedding rule-specific categories.
"""


class SourceMemberClassification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    member: str = Field(min_length=1)
    classification: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
