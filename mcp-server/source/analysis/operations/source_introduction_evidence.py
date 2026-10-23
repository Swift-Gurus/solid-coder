from pydantic import BaseModel, ConfigDict, Field
from source.source_unit_identity import SourceUnitIdentity

"""
solid-name: SourceIntroductionEvidence
solid-category: model
solid-spec: [SPEC-057]
solid-description: Records verified newly introduced interface identities and the source-comparison evidence supporting that determination.
"""


class SourceIntroductionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    verified_interfaces: list[SourceUnitIdentity] = Field(default_factory=list)
    reasoning: str
    evidence: str
