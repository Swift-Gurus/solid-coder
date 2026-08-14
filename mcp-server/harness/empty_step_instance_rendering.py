"""Defines rendering of an empty-collection workflow instance."""

from __future__ import annotations

from typing import Protocol

from harness.models import StepDef, StepInstance


"""
solid-name: EmptyStepInstanceRendering
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-030]
solid-description: Contract for rendering an engine-completed instance for an empty workflow collection.
"""
class EmptyStepInstanceRendering(Protocol):
    def render(self, step: StepDef) -> StepInstance: ...
