"""Defines rendering of rule-selection values for audit output."""

from typing import Protocol


"""
solid-name: RuleValuesRendering
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for rendering typed rule-selection values into auditable text values.
"""
class RuleValuesRendering(Protocol):

    def render(self, values: list[object]) -> list[str]: ...
