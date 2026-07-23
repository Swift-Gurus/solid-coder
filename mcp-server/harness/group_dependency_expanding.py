"""
solid-name: GroupDependencyExpanding
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for expanding a dependency on a group alias into dependencies on every member of that group.
"""

from __future__ import annotations

from typing import Protocol


class GroupDependencyExpanding(Protocol):

    def expand(self, raw_steps: list[dict], alias_groups: dict[str, list[str]]) -> list[dict]: ...
