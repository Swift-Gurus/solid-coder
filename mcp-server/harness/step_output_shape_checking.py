"""Defines structural checking for submitted step-output containers."""

from typing import Protocol

from harness.step_instance import StepInstance


"""
solid-name: StepOutputShapeChecking
solid-category: abstraction
solid-spec: [SPEC-031, SPEC-039]
solid-description: Contract for checking submitted workflow instance outputs have object-map structure.
"""
class StepOutputShapeChecking(Protocol):
    def errors(
        self,
        ready: list[StepInstance],
        outputs: dict,
    ) -> list[str]: ...
