"""Defines workflow-step dependency checking."""

from __future__ import annotations

from typing import Protocol

from harness.graph_step_field_reading import GraphStepFieldReading
from harness.models import RunState


"""
solid-name: StepDependencyChecking
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-030]
solid-description: Contract for checking whether a workflow entry's dependencies are terminal.
"""
class StepDependencyChecking(Protocol):
    def dependencies_met(
        self,
        entry: GraphStepFieldReading,
        run_state: RunState,
    ) -> bool: ...
