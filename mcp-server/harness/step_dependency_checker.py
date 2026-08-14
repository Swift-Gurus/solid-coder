"""Checks workflow-step dependencies against reconstructed run state."""

from __future__ import annotations

from harness.models import RunState, StepDef
from harness.step_dependency_checking import StepDependencyChecking


"""
solid-name: StepDependencyChecker
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Determines whether every declared dependency of a workflow step is complete.
"""
class StepDependencyChecker(StepDependencyChecking):
    def dependencies_met(self, step: StepDef, run_state: RunState) -> bool:
        return all(dependency in run_state.completed for dependency in step.depends_on)
