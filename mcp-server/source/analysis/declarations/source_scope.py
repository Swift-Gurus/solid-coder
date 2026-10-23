"""Describes one enclosing lexical scope with source evidence."""

from pydantic import BaseModel, ConfigDict, Field
from source.analysis.declarations.source_scope_kind import SourceScopeKind
from source.source_line_range import SourceLineRange

"""
solid-name: SourceScope
solid-category: model
solid-spec: [SPEC-066]
solid-description: Preserves an enclosing scope's identity, structural kind, name, and source lines without selecting review rules.
"""


class SourceScope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity: str = Field(min_length=1)
    kind: SourceScopeKind
    name: str = Field(min_length=1)
    span: SourceLineRange
