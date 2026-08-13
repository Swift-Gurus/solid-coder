"""
solid-name: IncludeResolution
solid-category: model
solid-spec: [SPEC-027, SPEC-035]
solid-description: Captures expanded include steps, alias groups, traversal labels, and workflow provenance.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.include_alias_group import IncludeAliasGroup


@dataclass(frozen=True)
class IncludeResolution:
    steps: list[dict] = field(default_factory=list)
    alias_groups: list[IncludeAliasGroup] = field(default_factory=list)
    include_chain: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    workflow_ids: list[str] = field(default_factory=list)
