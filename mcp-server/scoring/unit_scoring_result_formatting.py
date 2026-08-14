"""Defines compatibility formatting for unit scoring results."""

from typing import Protocol

from scoring.unit_scoring_result import UnitScoringResult


"""
solid-name: UnitScoringResultFormatting
solid-category: abstraction
solid-description: Contract for formatting one typed unit scoring result for compatibility clients.
"""
class UnitScoringResultFormatting(Protocol):
    def format(self, result: UnitScoringResult) -> dict: ...
