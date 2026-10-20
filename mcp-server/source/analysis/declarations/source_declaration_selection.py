from pydantic import BaseModel, ConfigDict, Field

from findings.review_unit_kind import ReviewUnitKind
from source.analysis.declarations.source_scope_kind import SourceScopeKind


"""
solid-name: SourceDeclarationSelection
solid-category: model
solid-spec: [SPEC-066]
solid-description: Describes a structural declaration selection by kind, enclosing scope, and any matching modifier without embedding review policy.
"""
class SourceDeclarationSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kinds: list[ReviewUnitKind] = Field(min_length=1)
    scopes: list[SourceScopeKind] = Field(default_factory=list)
    any_modifiers: list[str] = Field(default_factory=list)
