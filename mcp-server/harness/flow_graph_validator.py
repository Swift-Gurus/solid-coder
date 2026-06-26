"""
solid-description: Validates a flow's step definitions for structural integrity and consistency.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Protocol

from harness.models import FlowValidationError, StepDef


class FlowGraphValidating(Protocol):
    """
    solid-description: Contract for validating a flow's step definitions and raising errors for structural problems.
    solid-category: abstraction
    """

    def validate_raw(self, steps: list[dict]) -> None: ...
    def validate_for_each_references(self, steps: list[StepDef]) -> None: ...


class FlowGraphValidator:
    """
    solid-description: Validates a flow's step list for structural integrity and consistency.
    solid-category: service
    """

    def validate_raw(self, steps: list[dict]) -> None:
        seen_ids: set[str] = set()
        all_step_ids: set[str] = set()

        for step in steps:
            step_id = step.get("id")
            if not step_id:
                raise FlowValidationError("Step is missing required field 'id'")
            if step.get("prompt") is None:
                raise FlowValidationError(f"Step '{step_id}' is missing required field 'prompt'")
            if step_id in seen_ids:
                raise FlowValidationError(f"Duplicate step ID: '{step_id}'")
            seen_ids.add(step_id)
            all_step_ids.add(step_id)

        self._check_cycles(steps, all_step_ids)

    def validate_for_each_references(self, steps: list[StepDef]) -> None:
        step_outputs: dict[str, set[str]] = {
            step.id: {o.name for o in step.outputs}
            for step in steps
        }

        for step in steps:
            if step.for_each is None:
                continue
            expr = step.for_each.strip("{} ")
            parts = expr.split(".")
            if len(parts) >= 4 and parts[0] == "steps" and parts[2] == "outputs":
                dep_step_id = parts[1]
                output_name = parts[3]
                if dep_step_id not in step_outputs:
                    raise FlowValidationError(
                        f"Step '{step.id}' for_each references unknown step '{dep_step_id}'"
                    )
                if output_name not in step_outputs[dep_step_id]:
                    raise FlowValidationError(
                        f"Step '{step.id}' for_each references unknown output '{output_name}' on step '{dep_step_id}'"
                    )

    def _check_cycles(self, steps: list[dict], all_step_ids: set[str]) -> None:
        adjacency: dict[str, list[str]] = {s["id"]: [] for s in steps}
        in_degree: dict[str, int] = {s["id"]: 0 for s in steps}

        for step in steps:
            step_id = step["id"]
            deps = step.get("depends_on") or []
            for dep in deps:
                if dep not in all_step_ids:
                    raise FlowValidationError(
                        f"Step '{step_id}' depends on unknown step '{dep}'"
                    )
                adjacency[dep].append(step_id)
                in_degree[step_id] += 1

        queue = [sid for sid, deg in in_degree.items() if deg == 0]
        visited = 0
        while queue:
            node = queue.pop(0)
            visited += 1
            for neighbor in adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited != len(steps):
            raise FlowValidationError("Dependency cycle detected in flow steps")
