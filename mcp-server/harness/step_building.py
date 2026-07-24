"""
solid-description: Contract for converting input data into step specifications.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Protocol

from harness.models import StepDef


class StepBuilding(Protocol):
    """
    solid-description: Contract for converting input data into step specifications.
    solid-category: abstraction
    """

    def build(self, raw: dict) -> StepDef: ...