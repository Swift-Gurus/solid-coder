"""Defines rendering of executable workflow-step instances."""

from __future__ import annotations

from typing import Any, Protocol

from harness.models import StepDef, StepInstance


"""
solid-name: StepInstanceRendering
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-030]
solid-description: Contract for rendering standard and iterated workflow declarations as executable instances.
"""
class StepInstanceRendering(Protocol):
    def render_standard(
        self,
        step: StepDef,
        context: dict[str, Any],
    ) -> StepInstance: ...

    def render_iteration(
        self,
        step: StepDef,
        context: dict[str, Any],
        item: Any,
        iteration_index: int,
    ) -> StepInstance: ...
