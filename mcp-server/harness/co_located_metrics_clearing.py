"""Defines immutable clearing of expanded compact metrics."""

from typing import Protocol

from harness.step_declaration import StepDeclaration


"""
solid-name: CoLocatedMetricsClearing
solid-category: abstraction
solid-spec: [SPEC-058]
solid-description: Contract for removing compact measurements from their owner after typed expansion.
"""
class CoLocatedMetricsClearing(Protocol):
    def clear(self, owner: StepDeclaration) -> StepDeclaration: ...
