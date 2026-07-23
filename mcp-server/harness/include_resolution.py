"""
solid-name: IncludeResolution
solid-category: model
solid-spec: [SPEC-027]
solid-description: The result of resolving includes in a flow definition.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class IncludeResolution:
    steps: list[dict]
    alias_groups: dict[str, list[str]] = field(default_factory=dict)
    include_chain: list[str] = field(default_factory=list)
