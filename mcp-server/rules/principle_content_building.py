"""Defines assembly of one principle's detection content."""

from typing import Protocol


"""
solid-name: PrincipleContentBuilding
solid-category: abstraction
solid-description: Contract for assembling one discovered principle into structured detection instructions and metric examples.
"""
class PrincipleContentBuilding(Protocol):
    def build(self, principle_entry: dict) -> dict: ...
