"""Defines preparation of review input for pipeline tools."""

from typing import Protocol


"""
solid-name: ReviewInputPreparing
solid-category: abstraction
solid-description: Contract for preparing model-facing review input from current project changes.
"""
class ReviewInputPreparing(Protocol):
    def prepare(self, candidate_tags=None) -> dict: ...
