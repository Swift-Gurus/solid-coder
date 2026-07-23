"""
solid-name: GroupDependencyExpander
solid-category: service
solid-spec: [SPEC-027]
solid-description: Expands group-based step dependency references into explicit member step references.
"""

from __future__ import annotations

from harness.group_dependency_expanding import GroupDependencyExpanding


class GroupDependencyExpander(GroupDependencyExpanding):

    def expand(self, raw_steps: list[dict], alias_groups: dict[str, list[str]]) -> list[dict]:
        expanded = []
        for step in raw_steps:
            deps = step.get("depends_on") or []
            new_deps: list[str] = []
            for dep in deps:
                new_deps.extend(alias_groups.get(dep, [dep]))
            if new_deps == deps:
                expanded.append(step)
            else:
                updated = dict(step)
                updated["depends_on"] = new_deps
                expanded.append(updated)
        return expanded
