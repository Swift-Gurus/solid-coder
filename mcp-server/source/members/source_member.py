"""Defines one direct source member with deterministic source evidence."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from source.analysis.signatures.source_associated_type_signature import SourceAssociatedTypeSignature
from source.analysis.signatures.source_callable_signature import SourceCallableSignature
from source.analysis.signatures.source_subscript_signature import SourceSubscriptSignature
from source.analysis.signatures.source_unresolved_signature import SourceUnresolvedSignature
from source.analysis.signatures.source_value_signature import SourceValueSignature
from source.members.source_member_kind import SourceMemberKind
from source.members.source_member_visibility import SourceMemberVisibility
from source.source_line_range import SourceLineRange


SourceMemberSignature = Annotated[
    SourceCallableSignature | SourceValueSignature | SourceAssociatedTypeSignature | SourceSubscriptSignature | SourceUnresolvedSignature,
    Field(discriminator="kind"),
]


"""
solid-name: SourceMember
solid-category: model
solid-spec: [SPEC-062, SPEC-057]
solid-description: Records an ordered declaration member with stable identity, kind, visibility, typed signature facts, and source line evidence for downstream workflow selection.
"""
class SourceMember(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: SourceMemberKind
    visibility: SourceMemberVisibility
    span: SourceLineRange
    signature: SourceMemberSignature = Field(default_factory=SourceUnresolvedSignature)
