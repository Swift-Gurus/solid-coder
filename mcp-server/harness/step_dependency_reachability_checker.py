"""Checks transitive workflow-step dependencies."""

from __future__ import annotations

from harness.models import StepDef
from harness.step_dependency_reachability_checking import StepDependencyReachabilityChecking


"""
solid-name: StepDependencyReachabilityChecker
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Determines whether a workflow step reaches a source through declared dependencies.
"""
class StepDependencyReachabilityChecker(StepDependencyReachabilityChecking):
    def is_dependency(
        self,
        source_step_id: str,
        target_step: StepDef,
        steps: list[StepDef],
    ) -> bool:
        pending = list(target_step.depends_on)
        visited: set[str] = set()
        while pending:
            dependency_id = pending.pop(0)
            if dependency_id == source_step_id:
                return True
            if dependency_id in visited:
                continue
            visited.add(dependency_id)
            dependency = next(
                (step for step in steps if step.id == dependency_id),
                None,
            )
            if dependency is not None:
                pending.extend(dependency.depends_on)
        return False
