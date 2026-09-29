"""Defines validation of typed compact-metric owners."""

from typing import Protocol

from harness.step_declaration import StepDeclaration


"""
solid-name: CoLocatedMetricOwnerValidating
solid-category: abstraction
solid-spec: [SPEC-058]
solid-description: Contract for validating that a workflow step may own co-located measurements.
"""
class CoLocatedMetricOwnerValidating(Protocol):
    def validate(self, owner: StepDeclaration) -> str: ...
