"""
solid-name: StepGraphValidator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Validates the structural integrity of a flow's step graph.
"""

from __future__ import annotations

from typing import Protocol

from harness.kahn_cycle_detector import CycleDetecting
from harness.models import FlowValidationError


class StepGraphValidating(Protocol):

    def validate_raw(self, steps: list[dict], alias_groups: dict[str, list[str]] | None = None) -> None: ...


class StepGraphValidator(StepGraphValidating):

    def __init__(self, cycle_detector: CycleDetecting) -> None:
        self._cycle_detector = cycle_detector

    def validate_raw(self, steps: list[dict], alias_groups: dict[str, list[str]] | None = None) -> None:
        seen_ids: set[str] = set()
        all_step_ids: set[str] = set()

        for step in steps:
            step_id = step.get("id")
            if not step_id:
                raise FlowValidationError("Step is missing required field 'id'")
            if step_id in seen_ids:
                raise FlowValidationError(f"Duplicate step ID: '{step_id}'")
            seen_ids.add(step_id)
            all_step_ids.add(step_id)

        self._check_cycles(steps, all_step_ids, set(alias_groups or {}))

    def _check_cycles(self, steps: list[dict], all_step_ids: set[str], alias_ids: set[str]) -> None:
        known_ids = all_step_ids | alias_ids
        adjacency: dict[str, list[str]] = {sid: [] for sid in known_ids}
        in_degree: dict[str, int] = {sid: 0 for sid in known_ids}

        for step in steps:
            step_id = step["id"]
            deps = step.get("depends_on") or []
            for dep in deps:
                if dep not in known_ids:
                    raise FlowValidationError(
                        f"Step '{step_id}' depends on unknown step '{dep}'"
                    )
                adjacency[dep].append(step_id)
                in_degree[step_id] += 1

        if self._cycle_detector.has_cycle(adjacency, in_degree):
            raise FlowValidationError("Dependency cycle detected in flow steps")
