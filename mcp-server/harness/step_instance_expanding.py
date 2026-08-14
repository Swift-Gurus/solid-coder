"""Defines runtime expansion of workflow-step instances."""

from __future__ import annotations

from typing import Any, Protocol

from harness.models import RunState, StepDef, StepInstance


"""
solid-name: StepInstanceExpanding
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-030]
solid-description: Contract for expanding one ready workflow declaration into executable step instances.
"""
class StepInstanceExpanding(Protocol):
    def expand(
        self,
        step: StepDef,
        context: dict[str, Any],
        run_state: RunState,
    ) -> list[StepInstance]: ...
