from pydantic import BaseModel, ConfigDict, Field

from findings.review_unit_kind import ReviewUnitKind
from source.analysis.operations.labeled_source_member import LabeledSourceMember
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: SourceDeclarationContext
solid-category: model
solid-spec: [SPEC-057]
solid-description: Preserves a resolved definition, eligible member contributions, model-facing source context, and explicit evidence limitations without assigning review policy.
"""
class SourceDeclarationContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    declaration: SourceUnitIdentity | None
    kind: ReviewUnitKind | None
    name: str = ""
    members: list[LabeledSourceMember] = Field(default_factory=list)
    context: str = ""
    limitations: list[str] = Field(default_factory=list)
