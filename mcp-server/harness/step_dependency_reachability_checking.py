"""Defines transitive workflow-step dependency checks."""

from __future__ import annotations

from typing import Protocol

from harness.models import StepDef


"""
solid-name: StepDependencyReachabilityChecking
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-030]
solid-description: Contract for checking whether one workflow step transitively depends on another.
"""
class StepDependencyReachabilityChecking(Protocol):
    def is_dependency(
        self,
        source_step_id: str,
        target_step: StepDef,
        steps: list[StepDef],
    ) -> bool: ...
