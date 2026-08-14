"""Defines rendering of specification ancestry context."""

from typing import Protocol


"""
solid-name: SpecContextRendering
solid-category: abstraction
solid-description: Contract for rendering specification ancestry as readable context.
"""
class SpecContextRendering(Protocol):
    def render(self, spec_number: str, specs: list[dict]) -> str: ...
