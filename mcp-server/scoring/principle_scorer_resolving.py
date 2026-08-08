"""Defines typed resolution of principle scorers."""

from typing import Protocol

from scoring.principle_scorer_resolution import PrincipleScorerResolution


"""
solid-name: PrincipleScorerResolving
solid-category: abstraction
solid-description: Contract for resolving server-authoritative metric scoring for a named review principle.
"""
class PrincipleScorerResolving(Protocol):
    def resolve(self, principle: str) -> PrincipleScorerResolution: ...
