"""Defines include membership used to resolve an iteration source identity."""

from dataclasses import dataclass, field


"""
solid-name: ForEachSourceIdentityScope
solid-category: model
solid-spec: [SPEC-030, SPEC-037]
solid-description: Identifies assembled workflow members and include aliases excluded while locating their owning scope.
"""
@dataclass(frozen=True)
class ForEachSourceIdentityScope:
    member_ids: list[str]
    excluded_aliases: list[str] = field(default_factory=list)
