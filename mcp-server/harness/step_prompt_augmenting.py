"""Defines workflow-step prompt augmentation."""

from __future__ import annotations

from typing import Protocol

from harness.step_declaration import StepDeclaration


"""
solid-name: StepPromptAugmenting
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for adding output requirements to a workflow-step prompt.
"""
class StepPromptAugmenting(Protocol):
    def augment(
        self,
        step: StepDeclaration,
        requirements: list[str],
    ) -> StepDeclaration: ...
