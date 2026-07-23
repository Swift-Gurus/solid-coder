"""
solid-name: IncludeStructureValidator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Validates structural consistency of a flow's include definitions.
"""

from __future__ import annotations

from typing import Protocol

from harness.kahn_cycle_detector import CycleDetecting
from harness.models import FlowValidationError


class IncludeStructureValidating(Protocol):

    def validate_includes(
        self,
        steps: list[dict],
        alias_groups: dict[str, list[str]],
        top_level_step_ids: set[str],
        include_chain: list[str],
    ) -> None: ...


class IncludeStructureValidator(IncludeStructureValidating):

    def __init__(self, cycle_detector: CycleDetecting) -> None:
        self._cycle_detector = cycle_detector

    def validate_includes(
        self,
        steps: list[dict],
        alias_groups: dict[str, list[str]],
        top_level_step_ids: set[str],
        include_chain: list[str],
    ) -> None:
        self._validate_aliases(alias_groups, top_level_step_ids)
        self._validate_group_opacity(steps, alias_groups)
        self._validate_include_chain(include_chain)

    def _validate_aliases(self, alias_groups: dict[str, list[str]], top_level_step_ids: set[str]) -> None:
        for alias in alias_groups:
            if alias in top_level_step_ids:
                raise FlowValidationError(
                    f"Include alias '{alias}' collides with an existing step ID"
                )

    def _validate_group_opacity(self, steps: list[dict], alias_groups: dict[str, list[str]]) -> None:
        owning_alias = {
            member: alias
            for alias, members in alias_groups.items()
            for member in members
        }
        for step in steps:
            step_id = step.get("id")
            for dep in step.get("depends_on") or []:
                dep_alias = dep.split(".", 1)[0] if "." in dep else None
                if dep_alias is None or dep_alias not in alias_groups:
                    continue
                if dep_alias != owning_alias.get(step_id):
                    raise FlowValidationError(
                        f"Step '{step_id}' may not depend on qualified reference '{dep}' "
                        f"from outside group '{dep_alias}'"
                    )

    def _validate_include_chain(self, chain: list[str]) -> None:
        if len(chain) < 2:
            return
        unique = list(dict.fromkeys(chain))
        adjacency: dict[str, list[str]] = {node: [] for node in unique}
        in_degree: dict[str, int] = {node: 0 for node in unique}
        for a, b in zip(chain, chain[1:]):
            adjacency[a].append(b)
            in_degree[b] += 1

        if self._cycle_detector.has_cycle(adjacency, in_degree):
            raise FlowValidationError(
                f"Circular include detected: {' -> '.join(chain)}"
            )
