"""Defines workflow-step dependency checking."""

from __future__ import annotations

from typing import Protocol

from harness.models import RunState, StepDef


"""
solid-name: StepDependencyChecking
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-030]
solid-description: Contract for checking whether every declared workflow-step dependency is complete.
"""
class StepDependencyChecking(Protocol):
    def dependencies_met(self, step: StepDef, run_state: RunState) -> bool: ...
