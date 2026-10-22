"""Associates existing declaration facts with their lexical ancestry."""

from pydantic import BaseModel, ConfigDict, Field

from source.analysis.declarations.source_scope import SourceScope
from source.analysis.declarations.source_scope_kind import SourceScopeKind
from source.source_unit import SourceUnit
from source.source_evidence import SourceEvidence


"""
solid-name: SourceScopedDeclaration
solid-category: model
solid-spec: [SPEC-066]
solid-description: Records a source-unique declaration identity, existing typed declaration facts, modifiers, and outermost-first lexical scopes.
"""
class SourceScopedDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity: str = Field(min_length=1)
    unit: SourceUnit
    scopes: list[SourceScope] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list)
    leading_comments: list[SourceEvidence] = Field(default_factory=list)
    signals: list[SourceEvidence] = Field(default_factory=list)
    scope_kind: SourceScopeKind = SourceScopeKind.FILE
