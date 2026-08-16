"""Checks workflow-step dependencies against reconstructed run state."""

from __future__ import annotations

from typing import cast

from harness.graph_step_field_reading import GraphStepFieldReading
from harness.models import RunState
from harness.step_dependency_checking import StepDependencyChecking


"""
solid-name: StepDependencyChecker
solid-category: service
solid-spec: [SPEC-010, SPEC-030, SPEC-037]
solid-description: Determines whether every declared dependency of a workflow step is terminal.
"""
class StepDependencyChecker(StepDependencyChecking):
    def dependencies_met(
        self,
        entry: GraphStepFieldReading,
        run_state: RunState,
    ) -> bool:
        dependency_ids = cast(list[str], entry.depends_on or [])
        return all(
            dependency in run_state.completed or dependency in run_state.skipped
            for dependency in dependency_ids
        )
