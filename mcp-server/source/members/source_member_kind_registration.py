"""Associates an external parser declaration kind with a member kind."""

from dataclasses import dataclass

from source.members.source_member_kind import SourceMemberKind


"""
solid-name: SourceMemberKindRegistration
solid-category: model
solid-spec: [SPEC-062]
solid-description: Associates a parser declaration identity with a language-neutral member kind for deterministic source decoding.
"""
@dataclass(frozen=True)
class SourceMemberKindRegistration:
    parser_kind: str
    member_kind: SourceMemberKind
